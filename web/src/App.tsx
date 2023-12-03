import './App.scss';
import React, { useState, useRef } from 'react';
import { Container, Image, Card } from 'react-bootstrap';
import { useBreakpoint } from './breakpoint';


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

const useConstructor: (constructor: () => void) => void = (cFunc) => {
    let hasRunRef = useRef<boolean>(false);
    if(!hasRunRef.current) {
        hasRunRef.current = true; 
        cFunc()
    }
}

const useImages: () => [() => Promise<void>, ImageStats] = () => {
    const [images, setImages] = useState<ImageStats>({});

    const loadImages = async () => {
        let response = await fetch("/images")
        if(response.status === 200){
            let imagesJson = await response.json()
            setImages(imagesJson)
        } else {
            throw new Error(`Bad response ${response.status}: ${response.statusText}`)
        }
    }

    return [loadImages, images];
}

export function App() {
  return (
    <Container className="app" fluid>
        <ImageCards></ImageCards>
    </Container>
  );
}


const ImageCards: React.FunctionComponent<{}> = (props) => {
    let [loadImages, images] = useImages();
    useConstructor(() => {
        loadImages();
    })
    //let breakpoint = useBreakpoint();



    let imageElements = Object.entries(images).map(([name, stat]) => {
        return (<Card style={{width: "15rem", margin: "1rem"}}>
            <Card.Img alt={name} src={stat.thumbnail.url} width="15rem"/>
            <Card.Body>
                <Card.Title>
                    {name}
                </Card.Title>
                
            </Card.Body>
        </Card>)
    });

    return (
        <div className="d-flex flex-row flex-wrap justify-content-center flex-grow-0 flex-shrink-0 ">
            {imageElements}
        </div>
    )
}
