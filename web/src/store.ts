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
    fps: number,
    brightness: number,
    name: string
} & ImageStat;

export type ImageStats = {[imageName: string]: {
    original: ImageStat,
    thumbnail: ImageStat
}}

const remoteSlice = createSlice({
    name: "remote",
    initialState: {
        lightbarSettings: {} as LightbarSettings,
        imageStats: {} as ImageStats,
        activeItem: {} as ActiveImageStat
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
        }
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

export const { setImageStats, setLightbarSettings, setActiveItem } = remoteSlice.actions;
