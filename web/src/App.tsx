import './App.scss';
import React, { useState, useRef, FunctionComponent } from 'react';
import { Container, Image, Card } from 'react-bootstrap';
import { useBreakpoint } from './breakpoint';
import { store, setImageStats, setLightbarSettings, selectImageStats, ImageStats, LightbarSettings, selectLightbarSettings } from './store';
import { Provider, useDispatch, useSelector } from 'react-redux';
import { RouterProvider, createBrowserRouter } from "react-router-dom";

const useConstructor: (constructor: () => void) => void = (cFunc) => {
    let hasRunRef = useRef<boolean>(false);
    if(!hasRunRef.current) {
        hasRunRef.current = true; 
        cFunc()
    }
}

const fetchImages = async () => {
    let response = await fetch("/images")
    if(response.status === 200){
        let imagesJson = await response.json()
        return imagesJson as ImageStats
    }
    throw new Error(`Bad response ${response.status}: ${response.statusText}`)
}

const fetchLightbarSettings = async () => {
    let response = await fetch("/lightbar-settings")
    if(response.status === 200){
        let lightbarSettings = await response.json()
        return lightbarSettings as LightbarSettings
    }
    throw new Error(`Bad response ${response.status}: ${response.statusText}`)
}

const Index: FunctionComponent<{}> = () => {
    return (
        <Container className="app" fluid>
            <ImageCards/>
        </Container>
    )
}

const router = createBrowserRouter([
    {
        path: "/",
        element: <Index/>
    }
]);

export const App: FunctionComponent<{}> = () => {
    return (
        <Provider store={store}>
            <RouterProvider router={router}/>
        </Provider>
    );
}

const ImageCards: FunctionComponent<{}> = () => {
    const dispatch = useDispatch();

    useConstructor(() => {
        fetchImages().then(images => dispatch(setImageStats(images)));
        fetchLightbarSettings().then(lightbarSettings => dispatch(setLightbarSettings(lightbarSettings)));
    })

    let images = useSelector(selectImageStats);
    let lightbarSettings = useSelector(selectLightbarSettings);

    let imageElements = Object.entries(images).map(([name, stat]) => {
        let size = stat.original.size;
        let color = lightbarSettings ? (size.height == lightbarSettings.num_pixels ? 'lime' : 'crimson') : undefined;
        return (<Card style={{width: "15rem", margin: "1rem"}}>
            <Card.Img alt={name} src={stat.thumbnail.url} width="15rem"/>
            <Card.Body>
                <Card.Title>
                    {name}
                </Card.Title>
                <Card.Text>
                    <p className="font-weight-bold" style={{color}}>{`${size.height} x ${size.width}`}</p>
                </Card.Text>
            </Card.Body>
        </Card>)
    });

    return (
        <div className="d-flex flex-row flex-wrap justify-content-center flex-grow-0 flex-shrink-0 ">
            {imageElements}
        </div>
    )
}
