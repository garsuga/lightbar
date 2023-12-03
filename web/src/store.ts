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
    url: string
}

export type ImageStats = {[imageName: string]: {
    original: ImageStat,
    thumbnail: ImageStat
}}

export type RemoteState = {
    imageStats: ImageStats,
    lightbarSettings: LightbarSettings
}

export type StoreState = {
    remote: RemoteState
}

const remoteSlice: Slice<RemoteState> = createSlice({
    name: "remote",
    initialState: {
        lightbarSettings: {} as LightbarSettings,
        imageStats: {} as ImageStats
    },
    reducers: {
        setImageStats: (state, {payload}: {payload: ImageStats}) => {
            state.imageStats = payload;
        },
        setLightbarSettings: (state, {payload}: {payload: LightbarSettings}) => {
            state.lightbarSettings = payload;
        }
    }
})

export const store: Store<StoreState> = configureStore({
    reducer: {
        remote: remoteSlice.reducer
    }
})

export const selectImageStats = (state: StoreState) => state.remote.imageStats;
export const selectLightbarSettings = (state: StoreState) => state.remote.lightbarSettings;

export const { setImageStats, setLightbarSettings } = remoteSlice.actions;
