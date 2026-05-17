import { ref, shallowRef } from 'vue'
import L from 'leaflet'

const BASEMAP = {
  satellite: 'https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
  dark: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  osm: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
}

export function useMap() {
  const mapInstance = shallowRef(null)
  const rasterLayer = shallowRef(null)
  const geoJsonLayer = shallowRef(null)
  const drawPolygon = shallowRef(null)
  const drawMarkers = shallowRef([])

  function init(containerId, options = {}) {
    const el = typeof containerId === 'string'
      ? document.getElementById(containerId)
      : containerId
    if (!el) return

    mapInstance.value = L.map(el, {
      center: options.center || [45.39, 126.33],
      zoom: options.zoom || 10,
      zoomControl: true,
      attributionControl: false,
    })

    const tiles = options.basemap || 'satellite'
    L.tileLayer(BASEMAP[tiles] || BASEMAP.satellite, {
      maxZoom: 18,
      // ArcGIS attribution required
      attribution: tiles === 'satellite'
        ? '© Esri, Maxar, Earthstar Geographics'
        : '© OpenStreetMap, © CartoDB',
    }).addTo(mapInstance.value)

    L.control.scale({ position: 'bottomleft', imperial: false }).addTo(mapInstance.value)
  }

  function setRasterTile(layerKey) {
    if (rasterLayer.value) {
      mapInstance.value?.removeLayer(rasterLayer.value)
      rasterLayer.value = null
    }
    if (!layerKey || !mapInstance.value) return

    rasterLayer.value = L.tileLayer(`/api/v1/raster/${layerKey}/tile/{z}/{x}/{y}?colormap=viridis`, {
      opacity: 0.65,
      maxZoom: 18,
      attribution: '',
    }).addTo(mapInstance.value)
  }

  function renderFields(fields, selectedId) {
    if (geoJsonLayer.value) {
      mapInstance.value?.removeLayer(geoJsonLayer.value)
    }
    if (!fields?.length) return

    const features = fields.map(f => {
      let geom
      try { geom = JSON.parse(f.geom) } catch { return null }
      return { ...geom, properties: { id: f.id, name: f.name, crop: f.crop_type } }
    }).filter(Boolean)

    geoJsonLayer.value = L.geoJSON(features, {
      style: feat => ({
        color: feat.properties.id === selectedId ? '#2EC85D' : '#8B5E3C',
        weight: feat.properties.id === selectedId ? 2.5 : 1.5,
        fillColor: feat.properties.id === selectedId ? '#2EC85D' : '#3B82F6',
        fillOpacity: feat.properties.id === selectedId ? 0.15 : 0.05,
      }),
      onEachFeature: (feat, layer) => {
        layer.bindTooltip(`${feat.properties.name} · ${feat.properties.crop || ''}`, {
          permanent: false, direction: 'top', offset: [0, -8],
        })
      },
    }).addTo(mapInstance.value)
  }

  function fitToField(field) {
    if (!field || !mapInstance.value) return
    try {
      const geom = JSON.parse(field.geom)
      const coords = geom.coordinates?.[0]
      if (coords) {
        const bounds = L.latLngBounds(coords.map(([lng, lat]) => [lat, lng]))
        mapInstance.value.fitBounds(bounds, { padding: [80, 80], maxZoom: 14 })
      }
    } catch {}
  }

  function onMapClick(callback) {
    mapInstance.value?.on('click', e => callback(e.latlng))
  }

  function cleanup() {
    if (mapInstance.value) {
      mapInstance.value.remove()
      mapInstance.value = null
    }
  }

  return {
    mapInstance, rasterLayer, geoJsonLayer, drawPolygon, drawMarkers,
    init, setRasterTile, renderFields, fitToField, onMapClick, cleanup,
  }
}
