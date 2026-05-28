import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

export default function EquityCurveChart({ data, height = 250 }) {
  const chartContainerRef = useRef(null)

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) return

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#1a1f2e' },
        textColor: '#8b949e',
      },
      grid: {
        vertLines: { color: '#2d3343' },
        horzLines: { color: '#2d3343' },
      },
      timeScale: {
        borderColor: '#2d3343',
      },
      rightPriceScale: {
        borderColor: '#2d3343',
      },
      width: chartContainerRef.current.clientWidth,
      height,
      crosshair: { mode: 0 },
    })

    const lineSeries = chart.addLineSeries({
      color: '#58a6ff',
      lineWidth: 2,
    })

    const equityData = data.map(d => ({
      time: d[0],
      value: d[1],
    }))
    lineSeries.setData(equityData)

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [data, height])

  return (
    <div ref={chartContainerRef} style={{ width: '100%' }} />
  )
}
