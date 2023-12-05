import './App.scss';
import React, { useRef, FunctionComponent, useState } from 'react';
import { Container, Card, Button, Row, Navbar, Modal, Form } from 'react-bootstrap';
import { store, setImageStats, setLightbarSettings, selectImageStats, ImageStats, LightbarSettings, selectLightbarSettings, ImageStat, ActiveImageStat, setActiveItem, selectActiveItem, DisplaySettings, setDisplaySettings, selectDisplaySettings } from './store';
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

const fetchDisplaySettings = async () => {
    let response = await fetch("/display-settings")
    if(response.status === 200){
        let displaySettings = await response.json()
        return displaySettings as DisplaySettings
    }
    throw new Error(`Bad response ${response.status}: ${response.statusText}`)
}

const Index: FunctionComponent<{}> = () => {
    const dispatch = useDispatch();

    useConstructor(() => {
        fetchImages().then(images => dispatch(setImageStats(images)));
        fetchLightbarSettings().then(lightbarSettings => dispatch(setLightbarSettings(lightbarSettings)));
        fetchActiveItem().then(activeImageStat => dispatch(setActiveItem(activeImageStat)));
        fetchDisplaySettings().then(displaySettings => dispatch(setDisplaySettings(displaySettings)));
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
    let displaySettings = useSelector(selectDisplaySettings)

    return (
        <Container className="col-lg-4 col-xl-2 col-xs-12 gx-5" fluid>
            <Row>
                <div className="col-12" style={{marginTop: "1rem", marginBottom: "1rem"}}>
                    <Card>
                        {activeItem && activeItem.url ? (
                            <>
                                <Card.Img className="pixel-image" src={activeItem.url}/>
                                <Card.Body>
                                    <Card.Title>
                                        {activeItem.name}
                                    </Card.Title>
                                    <Card.Text>
                                        {
                                            displaySettings && displaySettings.brightness && (
                                                <span style={{whiteSpace: "pre-line"}}>
                                                    {`Brightness: ${displaySettings.brightness * 100}\n`}
                                                    {`FPS: ${displaySettings.fps}`}
                                                </span>
                                            )
                                        }
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

const calculateNewSize = (size: {width: number, height: number}, numPixels: number): {width: number, height: number} => {
    let newWidth = Math.round(numPixels / size.height * size.width);
    return {
        width: newWidth,
        height: numPixels
    }
}

const ImageCards: FunctionComponent<{}> = () => {
    let images = useSelector(selectImageStats);
    let lightbarSettings = useSelector(selectLightbarSettings);

    let [selectedImage, updateSelectedImage] = useState<string | undefined>(undefined);

    let imageElements = Object.entries(images).sort(([aId, aValue], [bId, bValue]) => aValue.original.name.localeCompare(bValue.original.name)).map(([id, stat]) => {
        let size = stat.original.size;
        let needsResize = lightbarSettings && lightbarSettings.numPixels && size.height != lightbarSettings.numPixels;
        let color = !needsResize ? 'lime' : 'crimson';
        let newDims = needsResize ? calculateNewSize(size, lightbarSettings.numPixels) : size;
        
        return (
            <div className="col-lg-4 col-xs-12" style={{marginTop: "1rem", marginBottom: "1rem"}}>
                <a onClick={() => updateSelectedImage(id)}>
                    <Card>
                        <Card.Img className="pixel-image" alt={id} src={stat.thumbnail.url}/>
                        <Card.Body>
                            <Card.Title>
                                {stat.original.name}
                            </Card.Title>
                            <Card.Text>
                                <span className="font-weight-bold" style={{color}}>{`${size.height} x ${size.width}`}</span>
                                {needsResize && (<><span>&ensp;&#8594;&ensp;</span><span>{`${newDims.height} x ${newDims.width}`}</span></>)}
                            </Card.Text>
                        </Card.Body>
                    </Card>
                </a>
            </div>
        )
    });

    return (
        <>
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

            <SetActiveImageModal show={!!selectedImage} onHide={() => updateSelectedImage(undefined)} imageId={selectedImage} imageStat={selectedImage ? images[selectedImage].original : undefined}/>
        </>
    )
}

const resampleTypes = {
    NEAREST: "Nearest Neighbor (Sharp Corners)",
    BICUBIC: "Bi-Cubic (Soft Corners)",
    BILINEAR: "Bi-Linear",
    BOX: "Box",
    HAMMING: "Hamming",
    LANCZOS: "Lanczos"
}

const SetActiveImageModal: FunctionComponent<{show: boolean, onHide: () => void, imageId: string | undefined, imageStat: ImageStat | undefined}> = ({show, onHide, imageId, imageStat}) => {
    return (
        <Form>
            <Modal show={show} onHide={onHide}>
                {
                    imageId && imageStat && (
                        <>
                        
                            <Modal.Header>
                                <Modal.Title>
                                    Set as active?
                                </Modal.Title>
                            </Modal.Header>                            
                            <Modal.Body>
                                <Form.Group>
                                    <Form.Label>Resize Resampling</Form.Label>
                                    <Form.Switch defaultValue="NEAREST">
                                        {Object.entries(resampleTypes).map(([id, prettyName]) => (
                                            <option value={id}>{prettyName}</option>
                                        ))}
                                    </Form.Switch>
                                </Form.Group>
                            </Modal.Body>
                            <Modal.Footer>
                                <Button variant="secondary" onClick={() => onHide()}>
                                    Cancel
                                </Button>
                                <Button variant="primary">
                                    Submit
                                </Button>
                            </Modal.Footer>
                        </>
                    )
                }
            </Modal>
        </Form>
    )
}
