import { createSlice, configureStore, Slice, Store } from "@reduxjs/toolkit";

export type LightbarSettings = {
    numPixels: number,
    numPixelsEach: number,
    numUnits: number,
    devices: string[],
    speed: number,
    redIndex: number,
    greenIndex: number,
    blueIndex: number
}

export type ImageStat = {
    size: {
        width: number,
        height: number
    },
    name: string,
    url: string
}

export type ActiveImageStat = {
    name: string,
    id: string,
    resampling: string
} & ImageStat;

export type ImageStats = {[imageName: string]: {
    original: ImageStat,
    thumbnail: ImageStat
}}

export type DisplaySettings = {
    fps: number,
    brightness: number
}

const remoteSlice = createSlice({
    name: "remote",
    initialState: {
        lightbarSettings: {} as LightbarSettings,
        imageStats: {} as ImageStats,
        activeItem: {} as ActiveImageStat,
        displaySettings: {} as DisplaySettings
    },
    reducers: {
        setImageStats: (state, {payload}: {payload: ImageStats}) => {
            state.imageStats = payload;
        },
        setLightbarSettings: (state, {payload}: {payload: LightbarSettings}) => {
            state.lightbarSettings = payload;
        },
        setActiveItem: (state, {payload}: {payload: ActiveImageStat}) => {
            state.activeItem = payload
        },
        setDisplaySettings: (state, {payload}: {payload: DisplaySettings}) => {
            state.displaySettings = payload
        },
    }
})

export const store: Store = configureStore({
    reducer: {
        remote: remoteSlice.reducer
    }
})

export const selectImageStats = (state: any) => state.remote.imageStats as ImageStats;
export const selectLightbarSettings = (state: any) => state.remote.lightbarSettings as LightbarSettings;
export const selectActiveItem = (state: any) => state.remote.activeItem as ActiveImageStat;
export const selectDisplaySettings = (state: any) => state.remote.displaySettings as DisplaySettings;

export const { setImageStats, setLightbarSettings, setActiveItem, setDisplaySettings } = remoteSlice.actions;
