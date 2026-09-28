import { useState, useEffect, useRef, useCallback } from 'react';

export function useC2Stream(wsUrl = 'ws://localhost:8000/ws/operator') {
  const [agents, setAgents] = useState([]);
  const [terminalOutput, setTerminalOutput] = useState([]);
  const [status, setStatus] = useState('connecting'); // 'connecting' | 'open' | 'closed'
  const socketRef = useRef(null);
  const reconnectRef = useRef(null);
  const shouldReconnectRef = useRef(true);

  const connectRef = useRef(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      setStatus('open');
      console.log('[C2Stream] connected to', wsUrl);
    };

    ws.onclose = () => {
      setStatus('closed');
      console.warn('[C2Stream] disconnected');
      if (shouldReconnectRef.current) {
        reconnectRef.current = setTimeout(() => {
          setStatus('connecting');
          connectRef.current?.();
        }, 2000);
      }
    };

    ws.onerror = (err) => {
      console.error('[C2Stream] error', err);
      ws.close();
    };

    ws.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch (err) {
        console.error('[C2Stream] bad JSON:', event.data, err);
        return;
      }

      switch (data.type) {
        case 'AGENT_REGISTER':
          setAgents((prev) => [
            ...prev.filter((a) => a.agent_id !== data.agent.agent_id),
            data.agent,
          ]);
          break;

        case 'AGENT_HEARTBEAT':
          setAgents((prev) =>
            prev.map((a) =>
              a.agent_id === data.agent_id
                ? { ...a, last_check_in: data.ts || new Date().toISOString(), status: 'online' }
                : a
            )
          );
          break;

        case 'AGENT_DISCONNECT':
          setAgents((prev) =>
            prev.map((a) =>
              a.agent_id === data.agent_id ? { ...a, status: 'offline' } : a
            )
          );
          break;

        case 'TASK_QUEUED':
          setTerminalOutput((prev) => [
            ...prev,
            { ...data, kind: 'queued', ts: new Date().toISOString() },
          ]);
          break;

        case 'TASK_RESULT':
          setTerminalOutput((prev) => [
            ...prev,
            { ...data, kind: 'result', ts: new Date().toISOString() },
          ]);
          break;

        default:
          console.debug('[C2Stream] unhandled event:', data);
      }
    };
  }, [wsUrl]);

  useEffect(() => {
    connectRef.current = connect;
    shouldReconnectRef.current = true;
    connect();

    return () => {
      shouldReconnectRef.current = false;
      clearTimeout(reconnectRef.current);
      socketRef.current?.close();
    };
  }, [connect]);

  const sendCommand = useCallback((agentId, command) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({ action: 'exec', agent_id: agentId, command })
      );
      return true;
    }
    console.warn('[C2Stream] cannot send — socket not open');
    return false;
  }, []);

  return { agents, terminalOutput, sendCommand, status };
}
