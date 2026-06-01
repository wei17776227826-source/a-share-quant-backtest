import { useEffect, useRef } from 'react'
import { createChart, LineSeries, AreaSeries, LineStyle, ColorType } from 'lightweight-charts'

export default function EquityCurveChart({ data, height = 250 }) {
  const chartContainerRef = useRef(null)

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
        timeVisible: false,
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

    // 数据格式兼容: 支持 [{date, equity}] 和 [时间戳, 数值] 两种格式
    const initialCapital = typeof data[0] === 'object' && data[0] !== null && 'equity' in data[0]
      ? parseFloat(data[0].equity)
      : 100000

    const seriesData = data.map((d, i) => {
      if (typeof d === 'object' && d !== null && 'equity' in d) {
        const baseTs = new Date(d.date || '2024-01-01').getTime() / 1000
        return {
          time: Math.floor(baseTs + i * 86400),
          value: parseFloat(d.equity) || initialCapital,
        }
      }
      // 数组格式 [timestamp, value]
      return { time: d[0], value: d[1] }
    })

    // 基准线（初始资金水平线）
    const baselineSeries = chart.addSeries(LineSeries, {
      color: '#2d3343',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      lastValueVisible: false,
      priceFormat: { type: 'price', precision: 0, minMove: 1 },
    })
    baselineSeries.setData(seriesData.map(d => ({ time: d.time, value: initialCapital })))

    // 主收益曲线（折线）
    const lineSeries = chart.addSeries(LineSeries, {
      color: '#58a6ff',
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      crosshairMarkerBackgroundColor: '#58a6ff',
      priceFormat: { type: 'price', precision: 0, minMove: 1 },
    })
    lineSeries.setData(seriesData)

    // 填充区域（渐变）
    const areaSeries = chart.addSeries(AreaSeries, {
      lineColor: '#58a6ff',
      topColor: 'rgba(88,166,255,0.15)',
      bottomColor: 'rgba(88,166,255,0.01)',
      lineWidth: 0,
      priceFormat: { type: 'price', precision: 0, minMove: 1 },
    })
    areaSeries.setData(seriesData)

    chart.timeScale().fitContent()

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
