import { reactive, provide, inject } from 'vue'

const STORE_KEY = Symbol('appStore')
const SELECT_FIELD_KEY = Symbol('selectFieldAndLoad')

function createStore() {
  const state = reactive({
    fields: [],
    selectedField: null,
    activeLayers: ['landuse'],
    basemap: 'satellite',
    soilProfile: null,
    weather: null,
    forecast: null,
    agriWeather: null,
    decision: null,
    ndviData: [],
    ndviTimeline: [],
    timelineIndex: 0,
    drawMode: false,
    drawVertices: [],
    shouldStartDraw: false,
    loading: false,
    clickedPoint: null,
    landCover: null,
    // 算法结果
    phenology: null,
    landEval: null,
    carbonModel: null,
    machineryPath: null,
  })

  const actions = {
    setFields(v) { state.fields = v },
    selectField(f) {
      state.selectedField = f
      if (f) {
        state.soilProfile = null
        state.weather = null
        state.decision = null
        state.forecast = null
        state.agriWeather = null
        state.landCover = null
        state.ndviData = []
        state.clickedPoint = null
      }
    },
    toggleLayer(key) {
      const idx = state.activeLayers.indexOf(key)
      if (idx >= 0) state.activeLayers.splice(idx, 1)
      else state.activeLayers.push(key)
    },
    setBasemap(v) { state.basemap = v },
    setSoilProfile(d) { state.soilProfile = d },
    setWeather(d) { state.weather = d },
    setForecast(d) { state.forecast = d },
    setAgriWeather(d) { state.agriWeather = d },
    setDecision(d) { state.decision = d },
    setNdvData(d) { state.ndviData = d },
    setNdvTimeline(d) { state.ndviTimeline = d },
    setTimelineIndex(i) { state.timelineIndex = i },
    startDraw() { state.drawMode = true; state.drawVertices = [] },
    addVertex(ll) { state.drawVertices = [...state.drawVertices, ll] },
    finishDraw() { state.drawMode = false; state.drawVertices = [] },
    cancelDraw() { state.drawMode = false; state.drawVertices = [] },
    triggerDraw() { state.shouldStartDraw = !state.shouldStartDraw },
    setLoading(v) { state.loading = v },
    setClickedPoint(point) { state.clickedPoint = point },
    setLandCover(d) { state.landCover = d },
    setAlgoResults(d) {
      if (d.phenology) state.phenology = d.phenology
      if (d.land_evaluation) state.landEval = d.land_evaluation
      if (d.carbon_prediction) state.carbonModel = d.carbon_prediction
      if (d.machinery_path) state.machineryPath = d.machinery_path
    },
  }

  return { state, ...actions }
}

export function provideStore() {
  const store = createStore()
  provide(STORE_KEY, store)
  return store
}

export function useAppStore() {
  const store = inject(STORE_KEY)
  if (!store) throw new Error('appStore not provided')
  return store
}

export function provideSelectFieldFn(fn) {
  provide(SELECT_FIELD_KEY, fn)
}

export function useSelectFieldFn() {
  return inject(SELECT_FIELD_KEY, null)
}
