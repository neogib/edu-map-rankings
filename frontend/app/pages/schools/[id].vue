<script setup lang="ts">
import type { SzkolaPublicWithRelations } from "~/types/schools"

const route = useRoute()
const schoolId = Number.parseInt(String(route.params.id), 10)

if (!Number.isInteger(schoolId) || schoolId <= 0) {
    throw createError({
        statusCode: 404,
        statusMessage: "Nieprawidłowy identyfikator szkoły",
    })
}

const {
    data: schoolData,
    status,
    error,
    refresh,
} = await useApi<SzkolaPublicWithRelations>(`/schools/${schoolId}`, {
    key: `school-details-${schoolId}`,
    lazy: true,
})

const school = computed(() => schoolData.value ?? null)

const isPending = computed(
    () => status.value === "pending" || status.value === "idle",
)
const hasError = computed(() => Boolean(error.value))

const hasLeftColumnContent = computed(() => {
    if (!school.value) return false

    return Boolean(
        (school.value.wynikiE8?.length ?? 0) ||
        (school.value.wynikiEm?.length ?? 0),
    )
})

useSeoMeta({
    title: () =>
        school.value
            ? `${school.value.nazwa} | EduRadar`
            : `Szkoła #${schoolId} | EduRadar`,
    description: () =>
        school.value
            ? `Szczegółowe dane szkoły ${school.value.nazwa}: wyniki egzaminów, rankingi i metadane.`
            : `Szczegółowe dane szkoły o identyfikatorze ${schoolId}.`,
})
</script>

<template>
    <UContainer class="max-w-7xl space-y-6 px-2 py-4 sm:px-5 lg:px-8">
        <SchoolDetailsPageSkeleton
            v-if="isPending && !school"
            :has-left-column-content="hasLeftColumnContent" />

        <div v-else-if="hasError" class="space-y-3">
            <UAlert
                color="error"
                variant="soft"
                title="Nie udało się pobrać danych szkoły"
                description="Spróbuj odświeżyć dane. Jeśli problem się powtarza, sprawdź połączenie z API." />
            <UButton
                color="error"
                variant="soft"
                icon="i-lucide-refresh-cw"
                @click="refresh()">
                Odśwież dane
            </UButton>
        </div>

        <UAlert
            v-else-if="!school"
            color="neutral"
            variant="soft"
            title="Brak danych szkoły"
            description="Nie znaleziono szczegółów dla podanego identyfikatora." />

        <div v-else class="space-y-6">
            <SchoolDetailsHeroCard :school="school" />

            <div
                class="grid grid-cols-1 gap-6"
                :class="hasLeftColumnContent ? 'lg:grid-cols-12' : ''">
                <div
                    v-if="hasLeftColumnContent"
                    class="min-w-0 space-y-6 lg:col-span-8">
                    <SchoolDetailsExamSection
                        :wyniki-e8="school.wynikiE8 ?? []"
                        :wyniki-em="school.wynikiEm ?? []" />
                </div>

                <div
                    class="min-w-0 space-y-6"
                    :class="hasLeftColumnContent ? 'lg:col-span-4' : ''">
                    <SchoolDetailsLocationCard :school="school" />
                    <SchoolDetailsRankingSection :school="school" />
                    <SchoolInfoCard :school="school" />
                </div>
            </div>
        </div>
    </UContainer>
</template>
