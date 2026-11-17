import { useCallback, useEffect, useState } from "react"
import { api } from "@/lib/api"

const EMPTY_STATE = {
    data: null,
    error: null,
    isLoading: false,
    requestKey: null,
}

/**
 * Load a GET endpoint with loading, error and retry states.
 * Requests are aborted when the page unmounts or the path changes.
 */
export function useApiData(path, { params } = {}) {
    const paramsKey = JSON.stringify(params ?? {})
    const requestKey = `${path}|${paramsKey}`
    const [state, setState] = useState(EMPTY_STATE)
    const [version, setVersion] = useState(0)

    useEffect(() => {
        let active = true
        const controller = new AbortController()

        api(path, {
            params: paramsKey === "{}" ? undefined : JSON.parse(paramsKey),
            signal: controller.signal,
        })
            .then((result) => {
                if (!active) return
                setState({
                    data: result,
                    error: null,
                    isLoading: false,
                    requestKey,
                })
            })
            .catch((raised) => {
                if (!active || raised.name === "AbortError") return
                setState({
                    data: null,
                    error: raised,
                    isLoading: false,
                    requestKey,
                })
            })

        return () => {
            active = false
            controller.abort()
        }
    }, [path, paramsKey, requestKey, version])

    const isCurrent = state.requestKey === requestKey
    const refetch = useCallback(() => {
        setState((current) => ({
            ...current,
            error: null,
            isLoading: true,
        }))
        setVersion((current) => current + 1)
    }, [])

    return {
        data: isCurrent ? state.data : null,
        error: isCurrent ? state.error : null,
        isLoading: !isCurrent || state.isLoading,
        refetch,
    }
}
