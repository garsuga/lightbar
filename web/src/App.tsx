import './App.scss';
import React, { useRef, FunctionComponent } from 'react';
import { Container, Card, Button, Row, Navbar } from 'react-bootstrap';
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
        <>
            <LightbarNavbar/>
            <Container className="app" fluid>
                <Row>
                    <ActiveImageInfo/>
                </Row>
                <Row>
                    <div className="col-lg-6 col-xs-10 mx-auto" style={{marginTop: "1rem", marginBottom: "1rem"}}>
                        <hr/>
                    </div>
                </Row>
                <Row>
                    <ImageCards/>
                </Row>
            </Container>
        </>
        
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

const LightbarNavbar: FunctionComponent<{}> = () => {
    let lightbarSettings = useSelector(selectLightbarSettings);

    return (
        <Navbar className="bg-body-tertiary" sticky='top'>
            <Container>
                <Navbar.Brand href="/">
                    Lightbar
                </Navbar.Brand>
                {
                    lightbarSettings && lightbarSettings.devices ? (
                        <>
                            <Navbar.Text>
                                {lightbarSettings.numPixels} px&emsp;{lightbarSettings.numUnits} strips&emsp;{lightbarSettings.speed} Hz
                            </Navbar.Text>
                        </>
                    ) : (
                        <Navbar.Text>
                            Loading...
                        </Navbar.Text>
                    )
                }
            </Container>
        </Navbar>
    )
}

const ActiveImageInfo: FunctionComponent<{}> = () => {
    
    let activeItem = useSelector(selectActiveItem);

    return (
        <Container className="col-lg-4 col-xl-2 col-xs-12 gx-5" fluid>
            <Row>
                <div className="col-12" style={{marginTop: "1rem", marginBottom: "1rem"}}>
                    <Card>
                        {activeItem && activeItem.url ? (
                            <>
                                <Card.Img src={activeItem.url}/>
                                <Card.Body>
                                    <Card.Title>
                                        <b>Active Item</b>&emsp;{activeItem.name}
                                    </Card.Title>
                                    <Card.Text>
                                        <span style={{whiteSpace: "pre-line"}}>
                                            {`Brightness: ${activeItem.brightness * 100}\n`}
                                            {`FPS: ${activeItem.fps}`}
                                        </span>
                                    </Card.Text>
                                    <Button>Change Display Settings</Button>
                                </Card.Body>
                            </>
                        ) : (
                            <Card.Body>
                                <Card.Title>
                                    No image selected...
                                </Card.Title>
                            </Card.Body>
                        )}
                    </Card>
                </div>
            </Row>
        </Container>
    )
}

const ImageCards: FunctionComponent<{}> = () => {
    let images = useSelector(selectImageStats);
    let lightbarSettings = useSelector(selectLightbarSettings);

    let imageElements = Object.entries(images).map(([name, stat]) => {
        let size = stat.original.size;
        let color = lightbarSettings && lightbarSettings.numPixels ? (size.height == lightbarSettings.numPixels ? 'lime' : 'crimson') : undefined;
        return (
            <div className="col-lg-4 col-xs-12" style={{marginTop: "1rem", marginBottom: "1rem"}}>
                <Card>
                    <Card.Img alt={name} src={stat.thumbnail.url}/>
                    <Card.Body>
                        <Card.Title>
                            {name}
                        </Card.Title>
                        <Card.Text>
                            <p className="font-weight-bold" style={{color}}>{`${size.height} x ${size.width}`}</p>
                        </Card.Text>
                    </Card.Body>
                </Card>
            </div>
        )
    });

    return (
        <Container className="col-lg-6 col-xs-12 gx-5" fluid>
            <Row>
                <h3 className="col-12">
                    Saved Images
                </h3>
            </Row>
            <Row>
                {imageElements}
            </Row>
        </Container>
    )
}
