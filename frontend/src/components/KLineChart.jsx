import { useEffect, useRef } from 'react'
import { createChart, LineSeries, CandlestickSeries, HistogramSeries, ColorType } from 'lightweight-charts'

export default function KLineChart({ data, height = 400 }) {
  const chartContainerRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) return

    const container = chartContainerRef.current
    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: '#1a1f2e' },
        textColor: '#8b949e',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#2d3343' },
        horzLines: { color: '#2d3343' },
      },
      timeScale: {
        borderColor: '#2d3343',
        tickMarkFormatter: (ts) => {
          const d = new Date(ts * 1000)
          return `${d.getMonth() + 1}/${d.getDate()}`
        },
      },
      rightPriceScale: {
        borderColor: '#2d3343',
      },
      width: container.clientWidth,
      height,
      handleScroll: false,
      handleScale: false,
    })

    // K 线数据
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#3fb950',
      downColor: '#f85149',
      borderDownColor: '#f85149',
      borderUpColor: '#3fb950',
      wickDownColor: '#f85149',
      wickUpColor: '#3fb950',
    })

    const candleData = data.map((d, i) => {
      // 日期转为时间戳
      let time = 0
      if (typeof d.date === 'string') {
        time = Math.floor(new Date(d.date).getTime() / 1000)
      } else if (typeof d.date === 'number') {
        time = d.date
      } else {
        time = i
      }
      return {
        time,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }
    })
    candleSeries.setData(candleData)

    // MA5 线
    const ma5Data = data
      .filter(d => d.ma5 !== null && d.ma5 !== undefined)
      .map((d, i) => ({
        time: typeof d.date === 'string' ? Math.floor(new Date(d.date).getTime() / 1000) : i,
        value: d.ma5,
      }))
    if (ma5Data.length > 0) {
      chart.addSeries(LineSeries, {
        color: '#58a6ff',
        lineWidth: 1,
        lastValueVisible: false,
        title: 'MA5',
      }).setData(ma5Data)
    }

    // MA10 线
    const ma10Data = data
      .filter(d => d.ma10 !== null && d.ma10 !== undefined)
      .map((d, i) => ({
        time: typeof d.date === 'string' ? Math.floor(new Date(d.date).getTime() / 1000) : i,
        value: d.ma10,
      }))
    if (ma10Data.length > 0) {
      chart.addSeries(LineSeries, {
        color: '#d29922',
        lineWidth: 1,
        lastValueVisible: false,
        title: 'MA10',
      }).setData(ma10Data)
    }

    // MA20 线
    const ma20Data = data
      .filter(d => d.ma20 !== null && d.ma20 !== undefined)
      .map((d, i) => ({
        time: typeof d.date === 'string' ? Math.floor(new Date(d.date).getTime() / 1000) : i,
        value: d.ma20,
      }))
    if (ma20Data.length > 0) {
      chart.addSeries(LineSeries, {
        color: '#8b949e',
        lineWidth: 1,
        lastValueVisible: false,
        title: 'MA20',
      }).setData(ma20Data)
    }

    // 成交量
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    })
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    })
    volumeSeries.setData(data.map((d, i) => ({
      time: typeof d.date === 'string' ? Math.floor(new Date(d.date).getTime() / 1000) : i,
      value: d.volume,
      color: d.close >= d.open ? 'rgba(63,185,80,0.3)' : 'rgba(248,81,73,0.3)',
    })))

    chartRef.current = chart

    const handleResize = () => {
      if (container) {
        chart.applyOptions({ width: container.clientWidth })
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
