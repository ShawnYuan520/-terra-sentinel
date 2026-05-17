import { shallowRef, onUnmounted } from 'vue'
import * as echarts from 'echarts'

export function useCharts() {
  const instances = []

  function initChart(dom, options) {
    if (!dom) return null
    const instance = echarts.init(dom)
    instance.setOption(options)
    instances.push(instance)

    const ro = new ResizeObserver(() => instance.resize())
    ro.observe(dom)

    return instance
  }

  function disposeAll() {
    instances.forEach(i => i.dispose())
    instances.length = 0
  }

  onUnmounted(() => disposeAll())

  return { initChart, disposeAll }
}
