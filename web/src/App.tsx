import './App.scss';
import React, { useRef, FunctionComponent } from 'react';
import { Container, Card, Button } from 'react-bootstrap';
import { store, setImageStats, setLightbarSettings, selectImageStats, ImageStats, LightbarSettings, selectLightbarSettings, ImageStat, ActiveImageStat, setActiveItem, selectActiveItem } from './store';
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

const fetchActiveItem = async () => {
    let response = await fetch("/active")
    if(response.status === 200){
        let activeStat = await response.json()
        return activeStat as ActiveImageStat
    }
    throw new Error(`Bad response ${response.status}: ${response.statusText}`)
}

const Index: FunctionComponent<{}> = () => {
    const dispatch = useDispatch();

    useConstructor(() => {
        fetchImages().then(images => dispatch(setImageStats(images)));
        fetchLightbarSettings().then(lightbarSettings => dispatch(setLightbarSettings(lightbarSettings)));
        fetchActiveItem().then(activeImageStat => dispatch(setActiveItem(activeImageStat)))
    })

    return (
        <Container className="app" fluid>
            <ImageAndLightbarInfo/>
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

const ImageAndLightbarInfo: FunctionComponent<{}> = () => {
    let lightbarSettings = useSelector(selectLightbarSettings);
    let activeItem = useSelector(selectActiveItem);

    return (
        <div className="d-flex flew-row flex-wrap justify-content-center">
            <Card>
                <Card.Body>
                    <Card.Title>
                        Lightbar Info
                    </Card.Title>
                    <Card.Body>
                        {lightbarSettings && lightbarSettings.devices ? (<>
                            <span style={{whiteSpace: "pre-line"}}>
                                {`Number of Devices: ${lightbarSettings.devices.length}\n`}
                                {`Device Speed: ${lightbarSettings.speed} Hz\n`}
                                {`Pixels / Device: ${lightbarSettings.numPixelsEach}\n`}
                                {`Total Pixels: ${lightbarSettings.numPixels}`}
                            </span>
                        </>) : (<>
                            Loading...
                        </>)}
                        
                    </Card.Body>
                </Card.Body>
            </Card>

            <Card>
                {activeItem && activeItem.url ? (
                    <>
                        <Card.Img src={activeItem.url}/>
                        <Card.Body>
                            <Card.Title>
                                Active Item: {activeItem.name}
                            </Card.Title>
                            <Card.Text>
                                <span style={{whiteSpace: "pre-line"}}>
                                    {`Brightness: ${activeItem.brightness}\n`}
                                    {`FPS: ${activeItem.fps}`}
                                </span>
                            </Card.Text>
                            <Button>Change Display Settings</Button>
                        </Card.Body>
                    </>
                ) : (
                    <Card.Body>
                        <Card.Title>

                        </Card.Title>
                    </Card.Body>
                )}
            </Card>
        </div>
    )
}

const ImageCards: FunctionComponent<{}> = () => {
    let images = useSelector(selectImageStats);
    let lightbarSettings = useSelector(selectLightbarSettings);

    let imageElements = Object.entries(images).map(([name, stat]) => {
        let size = stat.original.size;
        let color = lightbarSettings && lightbarSettings.numPixels ? (size.height == lightbarSettings.numPixels ? 'lime' : 'crimson') : undefined;
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
