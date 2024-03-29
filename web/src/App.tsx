import './App.scss';
import React, { useRef, FunctionComponent, useState } from 'react';
import { Container, Card, Button, Row, Navbar, Modal, Form } from 'react-bootstrap';
import { store, setImageStats, setLightbarSettings, selectImageStats, ImageStats, LightbarSettings, selectLightbarSettings, ImageStat, ActiveImageStat, setActiveItem, selectActiveItem, DisplaySettings, setDisplaySettings, selectDisplaySettings } from './store';
import { Provider, useDispatch, useSelector } from 'react-redux';
import { RouterProvider, createBrowserRouter } from "react-router-dom";
import { Dispatch } from '@reduxjs/toolkit';

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

const updateImages = (dispatch: Dispatch) => fetchImages().then(images => dispatch(setImageStats(images)));
const updateLightbarSettings = (dispatch: Dispatch) => fetchLightbarSettings().then(lightbarSettings => dispatch(setLightbarSettings(lightbarSettings)));
const updateActiveItem = (dispatch: Dispatch) => fetchActiveItem().then(activeImageStat => dispatch(setActiveItem(activeImageStat)));
const updateDisplaySettings = (dispatch: Dispatch) => fetchDisplaySettings().then(displaySettings => dispatch(setDisplaySettings(displaySettings)));

const Index: FunctionComponent<{}> = () => {
    const dispatch = useDispatch();

    useConstructor(() => {
        updateImages(dispatch);
        updateLightbarSettings(dispatch);
        updateActiveItem(dispatch);
        updateDisplaySettings(dispatch);
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

    let formatSpeed = (speed: number) => {
        debugger;
        let units = ["Hz", "KHz", "MHz", "GHz"]
        let ui = 0
        while(speed > 1000) {
            speed /= 1000;
            ui += 1
        }

        return `${speed} ${units[ui]}`
    }

    return (
        <>
            <Navbar className="bg-body-tertiary" sticky='top'>
                <Container>
                    <Navbar.Brand href="/">
                        Lightbar
                    </Navbar.Brand>
                    {
                        lightbarSettings && lightbarSettings.devices ? (
                            <>
                                <Navbar.Text>
                                    {lightbarSettings.numPixels} px&emsp;{lightbarSettings.numUnits} strips&emsp;{formatSpeed(lightbarSettings.speed)}
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
        </>
    )
}

const SetDisplaySettingsModal: FunctionComponent<{show: boolean, onHide: () => void}> = ({show, onHide}) => {
    let displaySettings = useSelector(selectDisplaySettings);
    let activeImageStat = useSelector(selectActiveItem);

    let [brightness, updateBrightness] = useState<number>();
    let [fps, updateFps] = useState<number>();
    let dispatch = useDispatch();
    if(!displaySettings) {
        return <></>
    }

    if(fps === undefined && displaySettings.fps !== undefined) {
        updateFps(displaySettings.fps);
    }

    if(brightness === undefined && displaySettings.brightness !== undefined) {
        updateBrightness(displaySettings.brightness * 100);
    }

    let submitForm = () => {
        fetch("/display-settings", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                fps,
                brightness: (brightness as number) / 100.0
            })
        }).then(() => updateDisplaySettings(dispatch));
    }

    let activeImageWidth = activeImageStat?.size?.width || 0;
    let activeDuration = fps ? (activeImageWidth / fps) : 0;
    let getFpsFromNewDuration = (dur: number) => {
        return Math.round(activeImageWidth/dur);
    }
    
    return (
        <Modal show={show} onHide={onHide}>
            <Form>
                <Modal.Header>
                    <Modal.Title>
                        Display Settings
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form.Group>
                        <Form.Label>
                            Brightness
                        </Form.Label>
                        <Form.Range min="1" max="100" step="1" value={brightness} onChange={ev => updateBrightness(parseFloat(ev.target.value))}/>
                        <Form.Label>{brightness}</Form.Label>
                    </Form.Group>
                    <Form.Group>
                        <Form.Label>
                            FPS
                        </Form.Label>
                        <Form.Range min="1" max="300" step="1" value={fps} onChange={ev => updateFps(Math.round(parseFloat(ev.target.value)))}/>
                        <Form.Label>{fps}</Form.Label>
                    </Form.Group>
                    <Form.Group>
                        <Form.Label>
                            Time (sec)
                        </Form.Label>
                        <Form.Range min={Math.log(activeImageWidth/300)} max={Math.log(activeImageWidth)} step={0.01} value={Math.log(activeDuration)} onChange={ev => updateFps(getFpsFromNewDuration(Math.exp(parseFloat(ev.target.value))))}/>
                        <Form.Label>{activeDuration.toFixed(2)}</Form.Label>
                    </Form.Group>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => onHide()}>
                        Cancel
                    </Button>
                    <Button variant="primary" onClick={() => {
                        onHide();
                        submitForm();
                    }}>
                        Submit
                    </Button>
                </Modal.Footer>
            </Form>
        </Modal>
    )
}

const ActiveImageInfo: FunctionComponent<{}> = () => {
    let [modalShown, updateModalShown] = useState<boolean>(false);
    
    let activeItem = useSelector(selectActiveItem);
    let displaySettings = useSelector(selectDisplaySettings)

    let displayLightbar = () => fetch("/display");

    return (
        <>
            <SetDisplaySettingsModal show={modalShown} onHide={() => updateModalShown(false)}/>
            <Container className="col-lg-4 col-xl-2 col-xs-12 gx-5" fluid>
                <Row>
                    <div className="col-12" style={{marginTop: "1rem", marginBottom: "1rem"}}>
                        <Card>
                            {activeItem && activeItem.url ? (
                                <>
                                    <Card.Img className="pixel-image" src={activeItem.url + `?id=${activeItem.id}`}/>
                                    <Card.Body>
                                        <Card.Title>
                                            {activeItem.name}
                                        </Card.Title>
                                        <Card.Text>
                                            {
                                                displaySettings && displaySettings.brightness && (
                                                    <span style={{whiteSpace: "pre-line"}}>
                                                        {`${activeItem.size.width} x ${activeItem.size.height}\n`}
                                                        {`Brightness: ${displaySettings.brightness * 100}\n`}
                                                        {`FPS: ${displaySettings.fps}\n`}
                                                        {`Duration: ${(activeItem.size.width / displaySettings.fps).toFixed(2)} seconds`}
                                                    </span>
                                                )
                                            }
                                        </Card.Text>
                                        <Button onClick={() => updateModalShown(true)} style={{marginRight: ".5rem"}}>Change Display Settings</Button>
                                        <Button onClick={() => displayLightbar()} variant="success">Display</Button>
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
        </>
    )
}

const calculateNewSize = (size: {width: number, height: number}, numPixels: number): {width: number, height: number} => {
    let newWidth = Math.round(numPixels / size.height * size.width);
    return {
        width: newWidth,
        height: numPixels
    }
}

const UploadImageModal: FunctionComponent<{show: boolean, onHide: () => void}> = ({show, onHide}) => {
    let [name, updateName] = useState<string | undefined>(undefined);
    let [file, updateFile] = useState<File | undefined>(undefined);
    let dispatch = useDispatch()

    let valid = !!name && name.trim().length > 0 && !!file;

    let submitForm = () => {
        let data = new FormData();
        data.append("file", file as File);
        data.append("name", name as string);
        fetch("/upload-image", {
            method: "POST",
            body: data
        }).then(() => {
            updateImages(dispatch)
        })
    }

    let fileNamePat = /.*\/(.+?)\..*/

    return (
        <Modal show={show} onHide={onHide}>
            <Form>
                <Modal.Header>
                    <Modal.Title>
                        Upload Image
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form.Group>
                        <Form.Control required type="file" onChange={ev => {
                            updateFile((ev as any).target.files[0])
                            if(!name){
                                let path = (ev.target.value as string).replace(/\\/gi, "/")
                                let res = fileNamePat.exec(path) as string[]
                                updateName(res[1]);
                            }
                        }}/>
                    </Form.Group>
                    <Form.Group>
                        <Form.Label>Name</Form.Label>
                        <Form.Control value={name} required onChange={ev => updateName(ev.target.value)}></Form.Control>
                    </Form.Group>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => onHide()}>
                        Cancel
                    </Button>
                    <Button disabled={!valid} variant="primary" onClick={() => {
                        onHide();
                        submitForm();
                    }}>
                        Upload
                    </Button>
                </Modal.Footer>
            </Form>
        </Modal>
    )
}

const ImageCards: FunctionComponent<{}> = () => {
    let images = useSelector(selectImageStats);
    let lightbarSettings = useSelector(selectLightbarSettings);

    let [selectedImage, updateSelectedImage] = useState<string | undefined>(undefined);
    let [uploadModalShown, updateUploadModalShown] = useState<boolean>(false);

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
                                <span className="font-weight-bold" style={{color}}>{`${size.width} x ${size.height}`}</span>
                                {needsResize && (<><span>&ensp;&#8594;&ensp;</span><span>{`${newDims.width} x ${newDims.height}`}</span></>)}
                            </Card.Text>
                        </Card.Body>
                    </Card>
                </a>
            </div>
        )
    });

    return (
        <>
            <UploadImageModal show={uploadModalShown} onHide={() => updateUploadModalShown(false)}/>
            <Container className="col-lg-6 col-xs-12 gx-5" fluid>
                <Row>
                    <h3 className="col-6">
                        Saved Images
                    </h3>
                    <Button className="col-6" onClick={() => updateUploadModalShown(true)}>Upload</Button>
                </Row>
                <Row>
                    {imageElements}
                </Row>
            </Container>

            <SetActiveImageModal show={!!selectedImage} onHide={() => updateSelectedImage(undefined)} imageId={selectedImage} imageStat={selectedImage ? images[selectedImage].original : undefined}/>
        </>
    )
}

const RESAMPLE_TYPES = {
    NEAREST: "Nearest Neighbor (Sharp Corners)",
    BICUBIC: "Bi-Cubic (Soft Corners)",
    BILINEAR: "Bi-Linear",
    BOX: "Box",
    HAMMING: "Hamming",
    LANCZOS: "Lanczos"
}

const SetActiveImageModal: FunctionComponent<{show: boolean, onHide: () => void, imageId: string | undefined, imageStat: ImageStat | undefined}> = ({show, onHide, imageId, imageStat}) => {
    let [resampling, updateResampling] = useState<string>();
    let dispatch = useDispatch();

    let submitForm = () => {
        fetch('/active', {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                resampling,
                imageId
            })
        }).then(() => updateActiveItem(dispatch))
    }

    return (
        <Modal show={show} onHide={onHide}>
            {
                imageId && imageStat && (
                    <>
                        <Form>
                            <Modal.Header>
                                <Modal.Title>
                                    Set as active?
                                </Modal.Title>
                            </Modal.Header>                            
                            <Modal.Body>
                                <Form.Group>
                                    <Form.Label>Resize Resampling</Form.Label>
                                    <Form.Select required id="resampling" defaultValue="NEAREST" value={resampling} onChange={ev => updateResampling(ev.target.value)}>
                                        {Object.entries(RESAMPLE_TYPES).map(([id, prettyName]) => (
                                            <option value={id}>{prettyName}</option>
                                        ))}
                                    </Form.Select>
                                </Form.Group>
                            </Modal.Body>
                            <Modal.Footer>
                                <Button variant="secondary" onClick={() => onHide()}>
                                    Cancel
                                </Button>
                                <Button variant="primary" onClick={() => {
                                    onHide();
                                    submitForm();
                                }}>
                                    Submit
                                </Button>
                            </Modal.Footer>
                        </Form>
                    </>
                )
            }
        </Modal>
    )
}
