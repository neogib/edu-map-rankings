<script setup lang="ts">
import type { SlideoverProps } from "@nuxt/ui"
import type { UseSwipeDirection } from "@vueuse/core"
import { useMediaQuery, usePointerSwipe } from "@vueuse/core"
import type { SzkolaPublicWithRelations } from "~/types/schools"

interface Props {
    selectedPoint: SzkolaPublicWithRelations
}

const props = defineProps<Props>()
const emit = defineEmits<{
    close: []
}>()
const isLgUp = useMediaQuery("(min-width: 1024px)")
const swipeTarget = shallowRef<HTMLElement | null>(null)
const isDismissedBySwipe = ref(false)

const swipe = usePointerSwipe(swipeTarget, {
    pointerTypes: ["touch", "pen"],
    onSwipeEnd(_: PointerEvent, direction: UseSwipeDirection) {
        const dragX = Math.max(0, swipe.distanceX.value)
        if (direction === "left" && dragX >= 100)
            isDismissedBySwipe.value = true
    },
})

const transform = computed(() => {
    if (isDismissedBySwipe.value) return "translateX(-100%)"
    if (!swipe.isSwiping.value) return "translateX(0)"

    const dragX = Math.max(0, swipe.distanceX.value)
    return `translateX(${-dragX}px)`
})

const contentProps = computed<NonNullable<SlideoverProps["content"]>>(
    // intentionally pass through DOM attrs/events to the underlying DialogContent.
    () =>
        ({
            ref: (el: Element | null) => {
                swipeTarget.value = el as HTMLElement | null
            },
            class: swipe.isSwiping.value
                ? ""
                : "transition-transform duration-200 ease-linear",
            onTransitionend: handleContentTransitionEnd,
            style: {
                transform: transform.value,
            },
        }) as unknown as NonNullable<SlideoverProps["content"]>,
)

const handleContentTransitionEnd = (event: Event) => {
    const transitionEvent = event as TransitionEvent

    if (
        isDismissedBySwipe.value &&
        transitionEvent.propertyName === "transform"
    ) {
        emit("close")
    }
}

const handleOpenChange = (open: boolean) => {
    if (!open) emit("close")
}

defineShortcuts({
    escape: {
        usingInput: true,
        handler: () => emit("close"),
    },
})

const isPublicSchool = (status: string) => {
    return !status.toLowerCase().includes("nie")
}

// computed property for selected point score color
const scoreColor = computed(() => {
    return props.selectedPoint ? getScoreColor(props.selectedPoint.wynik) : ""
})
</script>

<template>
    <USlideover
        side="left"
        :modal="!isLgUp"
        :dismissible="false"
        :transition="!isDismissedBySwipe"
        title="Szczegóły placówki"
        close-icon="i-mdi-close"
        :content="contentProps"
        :ui="{
            overlay: 'lg:hidden',
            body: 'overflow-x-auto p-0 sm:p-0',
        }"
        @update:open="handleOpenChange">
        <template #body>
            <div class="relative">
                <div
                    class="p-4 border-b border-default bg-linear-to-br from-blue-50 via-indigo-50 to-violet-50 dark:from-blue-950/75 dark:via-indigo-950/70 dark:to-violet-950/65">
                    <h3 class="text-xl font-bold text-highlighted mb-3">
                        {{ selectedPoint.nazwa }}
                    </h3>

                    <UButton
                        :to="`/schools/${selectedPoint.id}`"
                        color="primary"
                        variant="outline"
                        icon="i-lucide-arrow-up-right"
                        size="sm"
                        class="mb-3">
                        Zobacz pełny profil szkoły
                    </UButton>

                    <div class="flex flex-wrap gap-2 mb-4">
                        <UBadge
                            color="primary"
                            variant="soft"
                            class="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium">
                            <UIcon
                                name="i-mdi-school-outline"
                                class="size-3.5" />
                            {{ selectedPoint.typ.nazwa }}
                        </UBadge>

                        <UBadge
                            :color="
                                isPublicSchool(
                                    selectedPoint.statusPublicznoprawny.nazwa,
                                )
                                    ? 'success'
                                    : 'secondary'
                            "
                            variant="soft"
                            class="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium">
                            <UIcon
                                v-if="
                                    isPublicSchool(
                                        selectedPoint.statusPublicznoprawny
                                            .nazwa,
                                    )
                                "
                                name="i-mdi-check-decagram"
                                class="size-3.5" />
                            <UIcon v-else name="i-mdi-lock" class="size-3.5" />
                            {{ selectedPoint.statusPublicznoprawny.nazwa }}
                        </UBadge>
                    </div>

                    <div
                        v-if="
                            selectedPoint.wynik !== null &&
                            selectedPoint.wynik !== undefined
                        "
                        class="rounded-xl border border-default bg-default/95 p-4 shadow-sm dark:bg-elevated/70">
                        <div class="flex items-center justify-between">
                            <div>
                                <div
                                    class="mb-1 inline-flex items-center gap-1">
                                    <p
                                        class="text-xs text-muted uppercase tracking-wide">
                                        Wynik ogólny
                                    </p>
                                    <SidebarScoreInfoPopover />
                                </div>
                                <div class="flex items-baseline">
                                    <span
                                        :class="'text-3xl font-bold'"
                                        :style="{
                                            color: scoreColor,
                                        }">
                                        {{ selectedPoint.wynik.toFixed(2) }}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div
                            class="mt-3 h-2 w-full rounded-full bg-accented/80 dark:bg-accented/60">
                            <div
                                :class="[
                                    'h-2 rounded-full transition-all duration-500',
                                ]"
                                :style="{
                                    width: `${selectedPoint.wynik}%`,
                                    'background-color': scoreColor,
                                }" />
                        </div>
                    </div>
                </div>

                <SidebarRanking :selected-point="selectedPoint" />
                <SidebarExamResults
                    :wyniki-e8="selectedPoint.wynikiE8"
                    :wyniki-em="selectedPoint.wynikiEm" />
                <div class="border-b p-4">
                    <SchoolInfoCard :school="selectedPoint" />
                </div>
            </div>
        </template>
    </USlideover>
</template>
