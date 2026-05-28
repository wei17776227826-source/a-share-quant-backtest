import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

export default function KLineChart({ data, height = 400 }) {
  const chartContainerRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) return

    // 创建图表
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#1a1f2e' },
        textColor: '#8b949e',
      },
      grid: {
        vertLines: { color: '#2d3343' },
        horzLines: { color: '#2d3343' },
      },
      crosshair: {
        mode: 0,
      },
      timeScale: {
        borderColor: '#2d3343',
      },
      rightPriceScale: {
        borderColor: '#2d3343',
      },
      width: chartContainerRef.current.clientWidth,
      height,
    })

    // K 线数据
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#3fb950',
      downColor: '#f85149',
      borderDownColor: '#f85149',
      borderUpColor: '#3fb950',
      wickDownColor: '#f85149',
      wickUpColor: '#3fb950',
    })

    const candleData = data.map(d => ({
      time: d.date,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }))
    candleSeries.setData(candleData)

    // MA5 线
    const ma5Data = data
      .filter(d => d.ma5 !== null)
      .map(d => ({ time: d.date, value: d.ma5 }))
    if (ma5Data.length > 0) {
      chart.addLineSeries({
        color: '#58a6ff',
        lineWidth: 1,
        lastValueVisible: false,
        title: 'MA5',
      }).setData(ma5Data)
    }

    // MA10 线
    const ma10Data = data
      .filter(d => d.ma10 !== null)
      .map(d => ({ time: d.date, value: d.ma10 }))
    if (ma10Data.length > 0) {
      chart.addLineSeries({
        color: '#d29922',
        lineWidth: 1,
        lastValueVisible: false,
        title: 'MA10',
      }).setData(ma10Data)
    }

    // MA20 线
    const ma20Data = data
      .filter(d => d.ma20 !== null)
      .map(d => ({ time: d.date, value: d.ma20 }))
    if (ma20Data.length > 0) {
      chart.addLineSeries({
        color: '#8b949e',
        lineWidth: 1,
        lastValueVisible: false,
        title: 'MA20',
      }).setData(ma20Data)
    }

    // 成交量
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    })
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    })
    volumeSeries.setData(data.map(d => ({
      time: d.date,
      value: d.volume,
      color: d.close >= d.open ? 'rgba(63,185,80,0.3)' : 'rgba(248,81,73,0.3)',
    })))

    chartRef.current = chart

    // 自适应宽度
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
