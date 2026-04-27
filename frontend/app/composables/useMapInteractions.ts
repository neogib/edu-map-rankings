import { useDebounceFn } from "@vueuse/core"
import type maplibregl from "maplibre-gl"
import { MAP_CONFIG } from "~/constants/mapConfig"
import type { SzkolaPublicShort } from "~/types/schools"

export const useMapInteractions = (
    emit: (event: "point-clicked", schoolId: number | null) => void,
    popupCoordinates: Ref<[number, number] | undefined>,
) => {
    type SchoolVectorTileProperties = Omit<
        SzkolaPublicShort,
        "miejscowosc" | "latitude" | "longitude"
    >
    type SchoolVectorTileFeature = maplibregl.MapGeoJSONFeature & {
        properties: SchoolVectorTileProperties
    }
    type MapMouseLayerEvent = maplibregl.MapMouseEvent & {
        features?: maplibregl.MapGeoJSONFeature[]
    }

    let currentFeatureCoordinates: string | undefined = undefined
    const hoveredSchool: Ref<SchoolVectorTileProperties | null> = ref(null)
    const route = useRoute()
    const activeMap = shallowRef<maplibregl.Map | null>(null)

    // Track hovered feature IDs for feature-state
    let hoveredClusterId: number | null = null
    let selectedSchoolId: number | null = null
    let pendingSelectedSchoolId: number | null = null

    const [minLon, minLat, maxLon, maxLat] = MAP_CONFIG.polandBounds

    const inPoland = (lng: number, lat: number) =>
        lng >= minLon && lng <= maxLon && lat >= minLat && lat <= maxLat

    const setFeatureStateSafe = (
        map: maplibregl.Map,
        id: number,
        state: { hover?: boolean; clicked?: boolean },
    ): boolean => {
        if (!map.isStyleLoaded()) return false
        if (!map.getSource(MAP_CONFIG.sourceId)) return false

        map.setFeatureState(
            {
                source: MAP_CONFIG.sourceId,
                sourceLayer: MAP_CONFIG.martinSourceLayer,
                id,
            },
            state,
        )

        return true
    }

    const syncSelectedSchoolState = (map: maplibregl.Map) => {
        if (pendingSelectedSchoolId === null) {
            if (selectedSchoolId !== null) {
                setFeatureStateSafe(map, selectedSchoolId, { clicked: false })
            }
            selectedSchoolId = null
            return
        }

        if (
            selectedSchoolId !== null &&
            selectedSchoolId !== pendingSelectedSchoolId
        ) {
            setFeatureStateSafe(map, selectedSchoolId, { clicked: false })
        }

        if (
            setFeatureStateSafe(map, pendingSelectedSchoolId, { clicked: true })
        ) {
            selectedSchoolId = pendingSelectedSchoolId
        }
    }

    const setupMapEventHandlers = (map: maplibregl.Map) => {
        activeMap.value = map

        // Map move end to update URL
        map.on("moveend", () => handleMoveEnd(map))

        // Unclustered point hover and click
        map.on("mousemove", "unclustered-points", (e) =>
            handleMouseMove(map, e),
        )
        map.on("mouseleave", "unclustered-points", () => handleMouseLeave(map))
        map.on("click", "unclustered-points", (e) => handleClick(map, e))

        // Cluster click to zoom in
        map.on("click", "clusters", (e) => handleClusterClick(map, e))

        // Cluster hover effect
        map.on("mousemove", "clusters", (e) => {
            if (e.features && e.features.length > 0) {
                if (hoveredClusterId !== null) {
                    setFeatureStateSafe(map, hoveredClusterId, {
                        hover: false,
                    })
                }
                const hoveredId = Number(e.features[0]?.id)
                if (!Number.isFinite(hoveredId)) return
                hoveredClusterId = hoveredId
                setFeatureStateSafe(map, hoveredClusterId, { hover: true })
            }
        })
        map.on("mouseleave", "clusters", () => {
            map.getCanvas().style.cursor = ""
            if (hoveredClusterId !== null) {
                setFeatureStateSafe(map, hoveredClusterId, { hover: false })
                hoveredClusterId = null
            }
        })
        map.on("mouseenter", "clusters", () => {
            map.getCanvas().style.cursor = "pointer"
        })

        // Keep route-driven selection in sync across style/source readiness changes.
        map.on("styledata", () => syncSelectedSchoolState(map))
        map.on("sourcedata", (e) => {
            if (e.sourceId === MAP_CONFIG.sourceId && e.isSourceLoaded) {
                syncSelectedSchoolState(map)
            }
        })

        syncSelectedSchoolState(map)
    }

    const handleMoveEnd = (map: maplibregl.Map) => {
        const { lng, lat } = map.getCenter()
        const zoom = map.getZoom()

        updateQueryCenterZoomDebounced(lng, lat, zoom, map)
    }

    const handleMouseMove = (map: maplibregl.Map, e: MapMouseLayerEvent) => {
        const feature = e.features?.[0] as SchoolVectorTileFeature | undefined
        if (!feature) return

        const pointGeometry = feature.geometry
        if (pointGeometry.type !== "Point") return

        const featureCoordinates = pointGeometry.coordinates.toString()
        if (currentFeatureCoordinates !== featureCoordinates) {
            currentFeatureCoordinates = featureCoordinates

            // Change the cursor style as a UI indicator.
            map.getCanvas().style.cursor = "pointer"

            const coordinates = pointGeometry.coordinates.slice() as [
                number,
                number,
            ]
            // Update the hovered school data
            hoveredSchool.value = feature.properties

            // Ensure that if the map is zoomed out such that multiple
            // copies of the feature are visible, the popup appears
            // over the copy being pointed to.
            while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
                coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360
            }

            // Use the MglPopup component instead of native popup
            popupCoordinates.value = coordinates
        }
    }

    const handleMouseLeave = (map: maplibregl.Map) => {
        currentFeatureCoordinates = undefined
        map.getCanvas().style.cursor = ""
        popupCoordinates.value = undefined
        hoveredSchool.value = null
    }

    const handleClick = async (map: maplibregl.Map, e: MapMouseLayerEvent) => {
        const feature = e.features?.[0] as SchoolVectorTileFeature | undefined
        if (!feature) return
        if (feature.geometry.type !== "Point") return

        const clickedSchoolId = Number(feature.properties.id)

        if (selectedSchoolId !== null) {
            setFeatureStateSafe(map, selectedSchoolId, { clicked: false })

            // Clicking the same school toggles the sidebar closed.
            if (selectedSchoolId === clickedSchoolId) {
                selectedSchoolId = null
                emit("point-clicked", null)
                return
            }
        }
        selectedSchoolId = clickedSchoolId
        setFeatureStateSafe(map, selectedSchoolId, { clicked: true })
        emit("point-clicked", clickedSchoolId)
    }

    const handleClusterClick = async (
        map: maplibregl.Map,
        e: MapMouseLayerEvent,
    ) => {
        const features = map.queryRenderedFeatures(e.point, {
            layers: ["clusters"],
        })
        const firstFeature = features[0]
        if (
            !firstFeature ||
            !firstFeature.properties?.cluster_id ||
            firstFeature.geometry.type !== "Point"
        )
            return

        map.easeTo({
            center: firstFeature.geometry.coordinates as [number, number],
            zoom: Math.min(map.getZoom() + 2, MAP_CONFIG.maxZoom),
            duration: 150,
        })
    }

    // Update bbox in URL
    const updateQueryCenterZoomDebounced = useDebounceFn(
        async (x: number, y: number, zoom: number, map: maplibregl.Map) => {
            // if user moved outside of Poland bounds, reset to default center
            if (!inPoland(x, y)) {
                map.easeTo({
                    center: MAP_CONFIG.polandCenter,
                })
                return
            }
            // only handle naviagtion to map page
            // sometimes debounced function is called after leaving the page
            if (!window.location.pathname.startsWith("/map")) return
            await navigateTo(
                {
                    query: {
                        ...route.query,
                        x: x.toFixed(6),
                        y: y.toFixed(6),
                        z: zoom.toFixed(2),
                    },
                },
                { replace: true },
            )
        },
        300,
    )

    watch(
        [() => route.params.id, activeMap],
        ([paramSchoolId, map]) => {
            const schoolId = Number.parseInt(String(paramSchoolId), 10)
            const hasValidSchoolId = Number.isInteger(schoolId) && schoolId > 0

            if (!hasValidSchoolId) {
                pendingSelectedSchoolId = null
                if (map) syncSelectedSchoolState(map)
                return
            }

            pendingSelectedSchoolId = schoolId
            if (!map) return
            syncSelectedSchoolState(map)
        },
        { immediate: true },
    )

    return {
        setupMapEventHandlers,
        hoveredSchool,
    }
}
