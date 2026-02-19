import React, { useRef, useState, useCallback } from 'react'
import Webcam from 'react-webcam'

const videoConstraints = {
  width: 640,
  height: 480,
  facingMode: 'user'
}

export default function FaceScanner({ onCapture, disabled = false, label = 'Capture Face' }) {
  const webcamRef = useRef(null)
  const [stream, setStream] = useState(null)
  const [error, setError] = useState(null)
  const [capturing, setCapturing] = useState(false)
  
  const startCamera = useCallback(async () => {
    try {
      setError(null)
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: videoConstraints 
      })
      setStream(mediaStream)
    } catch (err) {
      console.error('Camera error:', err)
      setError('Camera access denied. Please allow permissions.')
    }
  }, [])
  
  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
    }
  }, [stream])
  
  const capture = useCallback(async () => {
    if (!webcamRef.current || disabled) return
    
    setCapturing(true)
    setError(null)
    
    try {
      const imageSrc = webcamRef.current.getScreenshot()
      
      if (!imageSrc) {
        throw new Error('Failed to capture image')
      }
      
      // Convert base64 to blob
      const response = await fetch(imageSrc)
      const blob = await response.blob()
      
      // Call parent handler
      await onCapture(blob)
      
    } catch (err) {
      console.error('Capture error:', err)
      setError(err.message || 'Capture failed')
    } finally {
      setCapturing(false)
    }
  }, [webcamRef, onCapture, disabled])
  
  React.useEffect(() => {
    return () => stopCamera()
  }, [stopCamera])
  
  return (
    <div className="face-scanner">
      {!stream ? (
        <div className="text-center">
          <button 
            onClick={startCamera}
            className="btn btn-primary"
            disabled={disabled}
          >
            📷 Start Camera
          </button>
        </div>
      ) : (
        <div className="video-container">
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            videoConstraints={videoConstraints}
            className={disabled ? 'disabled' : ''}
          />
          <div className="video-overlay hidden">
            {capturing && 'Processing...'}
          </div>
        </div>
      )}
      
      {stream && (
        <div className="btn-group mt-4" style={{ justifyContent: 'center' }}>
          <button 
            onClick={capture}
            className="btn btn-success"
            disabled={disabled || capturing}
          >
            {capturing ? '⏳' : '📸'} {label}
          </button>
          <button 
            onClick={stopCamera}
            className="btn btn-outline"
            disabled={capturing}
          >
            ✕ Stop
          </button>
        </div>
      )}
      
      {error && (
        <div className="message error mt-4">
          {error}
        </div>
      )}
    </div>
  )
}