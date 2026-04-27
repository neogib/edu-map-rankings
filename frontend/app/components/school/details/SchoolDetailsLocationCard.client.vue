<script setup lang="ts">
import { MAP_CONFIG } from "~/constants/mapConfig"
import type { SzkolaPublicWithRelations } from "~/types/schools"

interface Props {
    school: SzkolaPublicWithRelations
}

const props = defineProps<Props>()
const colorMode = useColorMode()

const hasCoordinates = computed(
    () =>
        props.school.latitude !== null &&
        props.school.longitude !== null &&
        Number.isFinite(props.school.latitude) &&
        Number.isFinite(props.school.longitude),
)

const mapCenter = computed<[number, number]>(() => {
    if (!hasCoordinates.value) return MAP_CONFIG.defaultCenter

    return [props.school.longitude as number, props.school.latitude as number]
})

const mapStyle = computed(() =>
    colorMode.value === "dark" ? MAP_CONFIG.darkStyle : MAP_CONFIG.lightStyle,
)

const mapRoute = computed(() => {
    if (!hasCoordinates.value) return `/map/schools/${props.school.id}`

    return {
        path: `/map/schools/${props.school.id}`,
        query: {
            x: mapCenter.value[0].toFixed(6),
            y: mapCenter.value[1].toFixed(6),
            z: "16.00",
        },
    }
})
</script>

<template>
    <UCard :ui="{ body: 'space-y-4' }">
        <template #header>
            <div class="flex items-center gap-2">
                <UIcon name="i-mdi-map-marker" class="size-4 text-primary" />
                <h4 class="text-sm font-semibold text-highlighted">
                    Lokalizacja na mapie
                </h4>
            </div>
        </template>

        <div
            class="overflow-hidden rounded-xl border border-default bg-muted/30">
            <div
                v-if="hasCoordinates"
                class="aspect-square w-full overflow-hidden bg-accented/20">
                <MglMap
                    :map-key="`school-location-${school.id}`"
                    :map-style="mapStyle"
                    :center="mapCenter"
                    :zoom="16"
                    :min-zoom="MAP_CONFIG.minZoom"
                    :max-zoom="MAP_CONFIG.maxZoom"
                    :box-zoom="false"
                    :attribution-control="false">
                    <MglMarker :coordinates="mapCenter" />
                </MglMap>
            </div>

            <div
                v-else
                class="flex aspect-square items-center justify-center p-4 text-center text-sm text-muted">
                Brak współrzędnych geograficznych dla tej szkoły.
            </div>
        </div>

        <UButton
            :to="mapRoute"
            color="primary"
            variant="soft"
            icon="i-lucide-map-pinned"
            block>
            Zobacz na mapie
        </UButton>
    </UCard>
</template>
