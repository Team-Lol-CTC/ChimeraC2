import { useState, useEffect, useRef, useCallback } from "react"

export function useC2Stream(wsUrl = "ws://127.0.0.1:8000/ws/operator") {
  const [agents, setAgents] = useState([])
  const [terminalOutput, setTerminalOutput] = useState([])
  const [status, setStatus] = useState("connecting")

  const socketRef = useRef(null)
  const reconnectRef = useRef(null)
  const shouldReconnectRef = useRef(true)
  const connectRef = useRef(null)

  const connect = useCallback(() => {
    if (
      socketRef.current &&
      socketRef.current.readyState !== WebSocket.CLOSED
    ) {
      return
    }

    const ws = new WebSocket(wsUrl)
    socketRef.current = ws

    ws.onopen = () => {
      setStatus("open")
      console.log("[C2Stream] connected to", wsUrl)
    }

    ws.onclose = () => {
      setStatus("closed")
      console.warn("[C2Stream] disconnected")

      if (shouldReconnectRef.current) {
        reconnectRef.current = setTimeout(() => {
          setStatus("connecting")
          connectRef.current?.()
        }, 2000)
      }
    }

    ws.onerror = (err) => {
      console.error("[C2Stream] error", err)
    }

    ws.onmessage = (event) => {
      let data

      try {
        data = JSON.parse(event.data)
      } catch (err) {
        console.error("[C2Stream] bad JSON:", event.data, err)
        return
      }

      switch (data.type) {
        case "AGENT_REGISTER":
          if (!data.agent?.agent_id) {
            return
          }

          setAgents((prev) => {
            const updated = prev.filter(
              (agent) => agent.agent_id !== data.agent.agent_id
            )

            return [...updated, data.agent]
          })

          break

        case "AGENT_HEARTBEAT":
          setAgents((prev) =>
            prev.map((agent) =>
              agent.agent_id === data.agent_id
                ? {
                    ...agent,
                    last_seen: data.ts || new Date().toISOString(),
                    status: "online",
                  }
                : agent
            )
          )

          break

        case "AGENT_DISCONNECT":
          setAgents((prev) =>
            prev.map((agent) =>
              agent.agent_id === data.agent_id
                ? {
                    ...agent,
                    status: "offline",
                  }
                : agent
            )
          )

          break

        case "TASK_QUEUED":
          setTerminalOutput((prev) => [
            ...prev,
            {
              ...data,
              kind: "queued",
              ts: new Date().toISOString(),
            },
          ])

          break

        case "TASK_RESULT": {
          const result = data.result || {}

          setTerminalOutput((prev) => [
            ...prev,
            {
              ...result,
              kind: "result",
              ts: new Date().toISOString(),
              output: result.output ?? result.decoded_output ?? "",
            },
          ])

          break
        }

        default:
          console.debug(
            "[C2Stream] unhandled event:",
            data
          )
      }
    }
  }, [wsUrl])

  useEffect(() => {
    connectRef.current = connect
    shouldReconnectRef.current = true

    connect()

    return () => {
      shouldReconnectRef.current = false
      clearTimeout(reconnectRef.current)

      if (socketRef.current) {
        socketRef.current.close()
        socketRef.current = null
      }
    }
  }, [connect])

  const sendCommand = useCallback((agentId, command) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          action: "exec",
          agent_id: agentId,
          command,
        })
      )

      return true
    }

    console.warn(
      "[C2Stream] cannot send — socket not open"
    )

    return false
  }, [])

  return {
    agents,
    terminalOutput,
    sendCommand,
    status,
  }
}