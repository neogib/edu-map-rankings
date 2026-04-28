import type { BoundingBox } from "~/types/boundingBox"
import teddyBearIconUrl from "~/assets/images/figures/sdf/teddy-bear.png"
import gearIconUrl from "~/assets/images/figures/sdf/gear.png"
import schoolIconUrl from "~/assets/images/figures/sdf/school.png"
import starIconUrl from "~/assets/images/figures/sdf/star.png"
import bookIconUrl from "~/assets/images/figures/sdf/book.png"

export const MAP_CONFIG = {
    lightStyle: "/map-styles/style-light-pl.json",
    darkStyle: "/map-styles/dark-style-pl.json",
    polandBounds: [14, 48.95, 24.2, 55] as [number, number, number, number],
    polandCenter: [19.355417, 52.191111] as [number, number],
    defaultBbox: {
        minLng: 20.7639,
        minLat: 52.1189,
        maxLng: 21.3901,
        maxLat: 52.3473,
    } as BoundingBox,
    defaultCenter: [21.008333, 52.232222] as [number, number],
    defaultZoom: 12,
    voivodeshipZoom: 10,
    maxZoom: 19,
    minZoom: 4,
    mapKey: "mainMap",
    sourceId: "schools",
    martinSourceLayer: "szkola_clustered",
} as const

export const SCHOOL_ICONS = {
    Przedszkole: "teddyBear",
    "Szkoła podstawowa": "book",
    "Liceum ogólnokształcące": "schoolSymbol",
    Technikum: "gear",
    default: "starSymbol",
} as const

export const ICONS = {
    teddyBear: teddyBearIconUrl,
    book: bookIconUrl,
    schoolSymbol: schoolIconUrl,
    gear: gearIconUrl,
    starSymbol: starIconUrl,
} as const
