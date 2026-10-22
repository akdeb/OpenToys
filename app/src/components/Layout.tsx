import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { useActiveUser } from '../state/ActiveUserContext';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useEffect, useState } from 'react';
import { X, Download, Laptop, Play, AudioLines, ChevronDown } from 'lucide-react';
import { convertFileSrc } from '@tauri-apps/api/core';
import { VoiceWsProvider, useVoiceWs } from '../state/VoiceWsContext';
import { globalPersonalityImageUrl, versionedRemoteUrl } from '../lib/remoteAssets';

const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'http://127.0.0.1:8000';

const LayoutInner = () => {
  const { activeUser } = useActiveUser();
  const location = useLocation();
  const navigate = useNavigate();
  const voiceWs = useVoiceWs();
  const [activePersonalityName, setActivePersonalityName] = useState<string | null>(null);
  const [activePersonalityImageSrc, setActivePersonalityImageSrc] = useState<string | null>(null);
  const [activePersonalityImageError, setActivePersonalityImageError] = useState(false);
  const [activeVoiceId, setActiveVoiceId] = useState<string | null>(null);
  const [deviceConnected, setDeviceConnected] = useState<boolean>(false);
  const [deviceSessionId, setDeviceSessionId] = useState<string | null>(null);
  const [downloadedVoiceIds, setDownloadedVoiceIds] = useState<Set<string>>(new Set());
  const [isStartingDevice, setIsStartingDevice] = useState(false);
  // Built-in voices of the active TTS model; empty when it clones from a reference clip.
  const [ttsBackend, setTtsBackend] = useState<string | null>(null);
  const [presetVoices, setPresetVoices] = useState<{ id: string; name: string }[]>([]);
  const [presetVoice, setPresetVoice] = useState<string>('');
  const personalityImageSrc = (p: any) => {
    if (!p) return null;
    if (p?.is_global) {
      const pid = p?.id != null ? String(p.id) : '';
      return pid ? globalPersonalityImageUrl(pid) : null;
    }
    const src = typeof p?.img_src === 'string' ? p.img_src.trim() : '';
    if (!src) return null;
    if (/^https?:\/\//i.test(src)) return versionedRemoteUrl(src);
    return convertFileSrc(src);
  };

  const localActive = voiceWs.isActive;
  const sessionActive = deviceConnected || localActive;
  const isEsp32View =
    location.pathname === '/test' && new URLSearchParams(location.search).get('view') === 'esp32';

  const statusLabel = sessionActive ? 'Chat in progress' : 'Ready on device';
  const statusDotClass = sessionActive ? 'led-on' : 'led-idle';
  const statusTextClass = sessionActive ? 'text-emerald-700' : 'text-gray-500';

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const ds = await api.getDeviceStatus().catch(() => null);
        if (!cancelled && ds) {
          setDeviceConnected(ds?.ws_status === 'connected');
          setDeviceSessionId(ds?.session_id || null);
        }

        const selectedId = activeUser?.current_personality_id;
        if (!selectedId) {
          if (!cancelled) setActivePersonalityName(null);
          return;
        }

        const ps = await api.getPersonalities(true).catch(() => []);
        const selected = ps.find((p: any) => p.id === selectedId);
        if (!cancelled) {
          setActivePersonalityName(selected?.name || null);
          setActiveVoiceId(selected?.voice_id ? String(selected.voice_id) : null);
          setActivePersonalityImageSrc(personalityImageSrc(selected));
          setActivePersonalityImageError(false);
        }
      } catch {
        // ignore
        if (!cancelled) {
          setActivePersonalityImageSrc(null);
          setActivePersonalityImageError(false);
        }
      }
    };

    load();
  }, [activeUser?.current_personality_id]);

  const personalityId = activeUser?.current_personality_id;

  useEffect(() => {
    let cancelled = false;
    const loadPresetVoices = async () => {
      try {
        const models = await api.getModels();
        const backend = String(models?.tts?.backend || '');
        const option = (models?.tts?.options || []).find((o: any) => o?.id === backend);
        const voices: { id: string; name: string }[] = option?.presetVoices || [];
        let chosen = '';
        if (voices.length && personalityId) {
          const saved = await api.getSetting(`preset_voice:${backend}:${personalityId}`).catch(() => null);
          const value = String(saved?.value || '');
          chosen = voices.some((v) => v.id === value) ? value : '';
        }
        if (cancelled) return;
        setTtsBackend(backend || null);
        setPresetVoices(voices);
        setPresetVoice(chosen);
      } catch {
        if (!cancelled) setPresetVoices([]);
      }
    };
    void loadPresetVoices();
    return () => {
      cancelled = true;
    };
  }, [personalityId, location.pathname]);

  const onPresetVoiceChange = (value: string) => {
    setPresetVoice(value);
    if (ttsBackend && personalityId) {
      void api.setSetting(`preset_voice:${ttsBackend}:${personalityId}`, value || null).catch(() => {});
    }
  };

  useEffect(() => {
    let cancelled = false;
    let retryTimer: number | null = null;
    let es: EventSource | null = null;
    const base = API_BASE.replace('localhost', '127.0.0.1').replace(/\/+$/, '');

    const start = () => {
      if (cancelled) return;
      try {
        es = new EventSource(`${base}/events/device`);
      } catch {
        retryTimer = window.setTimeout(start, 3000);
        return;
      }

      es.onmessage = (ev) => {
        if (cancelled) return;
        try {
          const data = JSON.parse(ev.data || '{}');
          setDeviceConnected(data?.ws_status === 'connected');
          setDeviceSessionId(data?.session_id || null);
        } catch {
          // ignore
        }
      };

      es.onerror = () => {
        if (cancelled) return;
        try {
          es?.close();
        } catch {
          // ignore
        }
        es = null;
        if (retryTimer == null) {
          retryTimer = window.setTimeout(start, 3000);
        }
      };
    };

    start();
    return () => {
      cancelled = true;
      if (retryTimer != null) window.clearTimeout(retryTimer);
      try {
        es?.close();
      } catch {
        // ignore
      }
      es = null;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const refreshDownloaded = async () => {
      try {
        const ids = await api.listDownloadedVoices();
        if (!cancelled) setDownloadedVoiceIds(new Set(Array.isArray(ids) ? ids : []));
      } catch {
        if (!cancelled) setDownloadedVoiceIds(new Set());
      }
    };

    const onExperienceUpdated = (ev: Event) => {
      const detail = (ev as CustomEvent<{ id?: string; name?: string; voice_id?: string }>).detail || {};
      const selectedId = activeUser?.current_personality_id;
      if (!selectedId || !detail?.id || String(detail.id) !== String(selectedId)) return;

      if (typeof detail.name === 'string' && detail.name.trim()) {
        setActivePersonalityName(detail.name.trim());
      }
      setActiveVoiceId(detail.voice_id ? String(detail.voice_id) : null);
      void refreshDownloaded();
    };

    window.addEventListener('experience:updated', onExperienceUpdated as EventListener);
    return () => {
      cancelled = true;
      window.removeEventListener('experience:updated', onExperienceUpdated as EventListener);
    };
  }, [activeUser?.current_personality_id]);

  useEffect(() => {
    let cancelled = false;
    const loadDownloaded = async () => {
      try {
        const ids = await api.listDownloadedVoices();
        if (!cancelled) setDownloadedVoiceIds(new Set(Array.isArray(ids) ? ids : []));
      } catch {
        if (!cancelled) setDownloadedVoiceIds(new Set());
      }
    };
    loadDownloaded();
    return () => {
      cancelled = true;
    };
  }, [activeVoiceId]);

  useEffect(() => {
    let cancelled = false;
    const refresh = async () => {
      try {
        const ids = await api.listDownloadedVoices();
        if (!cancelled) setDownloadedVoiceIds(new Set(Array.isArray(ids) ? ids : []));
      } catch {
        if (!cancelled) setDownloadedVoiceIds(new Set());
      }
    };

    const onDownloaded = () => {
      void refresh();
    };

    window.addEventListener('voice:downloaded', onDownloaded as EventListener);
    return () => {
      cancelled = true;
      window.removeEventListener('voice:downloaded', onDownloaded as EventListener);
    };
  }, []);

  const canStartChat =
    sessionActive || !activeVoiceId || downloadedVoiceIds.has(String(activeVoiceId));
  const needsVoiceDownload = Boolean(activeVoiceId) && !downloadedVoiceIds.has(String(activeVoiceId));

  useEffect(() => {
    const onDeleted = () => {
      navigate('/');
    };
    window.addEventListener('voicews:empty-session-deleted', onDeleted as EventListener);
    return () => {
      window.removeEventListener('voicews:empty-session-deleted', onDeleted as EventListener);
    };
  }, [navigate]);

  return (
    <div className="app-shell flex flex-col h-screen overflow-hidden">
      <div className="flex flex-1 min-h-0 overflow-hidden">
        <Sidebar />
        <main className={`flex-1 min-h-0 overflow-y-auto ${location.pathname === '/test' ? 'p-0 pb-36' : 'p-8 pb-36'}`}>
          <div className={`max-w-4xl mx-auto ${location.pathname === '/test' ? 'px-8 pt-0' : ''}`}>
            <Outlet />
          </div>

        {activeUser?.current_personality_id && (
          <div className="session-dock fixed bottom-0 z-20 left-64 right-0 pointer-events-none">
            <div className="session-dock-wrap max-w-4xl mx-auto px-8 pb-6 pointer-events-auto">
              <div className="session-dock-inner px-4 py-3">
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0 flex items-center gap-3">
                  {activePersonalityImageSrc && !activePersonalityImageError && (
                    <div className="w-11 h-11 rounded-[6px] overflow-hidden bg-white border border-gray-200">
                      <img
                        src={activePersonalityImageSrc}
                        alt=""
                        className="w-full h-full object-cover"
                        onError={() => setActivePersonalityImageError(true)}
                      />
                    </div>
                  )}
                  <div className="min-w-0">
                    <div className="label-mono flex items-center gap-2">
                      <span className={`led ${statusDotClass} ${sessionActive ? 'retro-blink' : ''}`} />
                      <span className={statusTextClass}>{statusLabel}</span>
                    </div>
                    <div className="mt-1 font-display font-bold text-[17px] text-black truncate">{activePersonalityName || '—'}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex flex-col items-end">
                    {!localActive && !isEsp32View && (
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          className="retro-btn retro-btn-green no-lift px-4 flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
                          onClick={async () => {
                            if (needsVoiceDownload && activeVoiceId) {
                              navigate(`/voices?voice_id=${encodeURIComponent(String(activeVoiceId))}`);
                              return;
                            }
                            if (!deviceConnected || !canStartChat || isStartingDevice) return;
                            try {
                              setIsStartingDevice(true);
                              await api.startDevice();
                              navigate('/test?view=esp32');
                            } catch (e) {
                              console.error("Failed to start ESP32 session:", e);
                            } finally {
                              setIsStartingDevice(false);
                            }
                          }}
                          disabled={(!deviceConnected || !canStartChat || isStartingDevice) && !needsVoiceDownload}
                          title={deviceConnected ? "Start on ESP32" : "Connect your Mac to ELATO first"}
                        >
                          {needsVoiceDownload ? <Download size={18} className="shrink-0" /> : <Play fill="currentColor" size={18} className="shrink-0" />}
                          {needsVoiceDownload ? 'Download voice' : isStartingDevice ? 'Starting' : 'Play'}
                        </button>
                        <button
                          type="button"
                          className="retro-btn retro-btn-purple no-lift w-10 h-[34px] p-0 flex items-center justify-center disabled:opacity-60 disabled:cursor-not-allowed"
                          onClick={() => {
                            if (needsVoiceDownload && activeVoiceId) {
                              navigate(`/voices?voice_id=${encodeURIComponent(String(activeVoiceId))}`);
                              return;
                            }
                            if (!canStartChat) return;
                            navigate('/test');
                            voiceWs.connect();
                          }}
                          disabled={!canStartChat && !needsVoiceDownload}
                          title="Preview on laptop"
                          aria-label="Preview on laptop"
                        >
                          {needsVoiceDownload ? <Download size={18} className="shrink-0" /> : <Laptop size={18} className="shrink-0" />}
                        </button>
                      </div>
                    )}
                    {!localActive && deviceConnected && isEsp32View && (
                      <button
                        type="button"
                        className="retro-btn retro-btn-outline no-lift px-4 py-2 text-sm flex items-center gap-2"
                        onClick={async () => {
                          try {
                            await api.disconnectDevice();
                            setDeviceConnected(false);
                            const sid = deviceSessionId;
                            if (sid) {
                              navigate(`/conversations?session=${encodeURIComponent(sid)}`);
                            } else {
                              navigate('/conversations');
                            }
                          } catch {
                            // ignore
                          }
                        }}
                      >
                        <X size={18} className="shrink-0" /> End
                      </button>
                    )}
                    {localActive && (
                      <button
                        type="button"
                        className="retro-btn retro-btn-outline no-lift px-4 py-2 text-sm flex items-center gap-2"
                        onClick={() => {
                          voiceWs.disconnect();
                          const sid = voiceWs.latestSessionId;
                          if (sid) {
                            navigate(`/conversations?session=${encodeURIComponent(sid)}`);
                          } else {
                            navigate('/conversations');
                          }
                        }}
                      >
                        <X size={18} className="shrink-0" /> End
                      </button>
                    )}
                  </div>
                </div>
                </div>
                <div className="mt-2.5 pt-2 border-t border-gray-100 flex items-center justify-between gap-3 text-[11px] leading-tight font-mono text-gray-500">
                  {presetVoices.length > 0 ? (
                    <label
                      className="relative shrink-0 flex items-center gap-1 cursor-pointer hover:text-gray-800"
                      title="This model can't clone voices, so pick one of its built-in voices"
                    >
                      <AudioLines size={12} className="shrink-0" />
                      <span className="max-w-[130px] truncate">
                        {presetVoices.find((v) => v.id === presetVoice)?.name || 'Default voice'}
                      </span>
                      <ChevronDown size={11} className="shrink-0" />
                      <select
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        value={presetVoice}
                        onChange={(e) => onPresetVoiceChange(e.target.value)}
                        aria-label="Preset voice"
                      >
                        <option value="">Default voice</option>
                        {presetVoices.map((v) => (
                          <option key={v.id} value={v.id}>
                            {v.name}
                          </option>
                        ))}
                      </select>
                    </label>
                  ) : (
                    <span />
                  )}
                  <span className="truncate">Models can be wrong — verify important information.</span>
                  {presetVoices.length > 0 ? <span className="shrink-0 w-[1px]" /> : <span />}
                </div>
              </div>
            </div>
          </div>
        )}
        </main>
      </div>
    </div>
  );
};

export const Layout = () => {
  return (
    <VoiceWsProvider>
      <LayoutInner />
    </VoiceWsProvider>
  );
};
