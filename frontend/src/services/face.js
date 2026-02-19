/**
 * Face recognition service
 */
import api, { uploadFile } from './api'

export const faceService = {
  /**
   * Enroll user's face
   * @param {Blob} photo - Image blob from camera
   */
  enroll: async (photo) => {
    return uploadFile('/face/enroll', photo)
  },
  
  /**
   * Recognize face for attendance
   * @param {Blob} photo - Current frame
   * @param {string} courseCode - Course identifier
   */
  recognize: async (photo, courseCode) => {
    return uploadFile('/face/recognize', photo, { course_code: courseCode })
  },
  
  /**
   * Test face detection (development)
   */
  test: async (photo) => {
    return uploadFile('/face/test', photo)
  }
}

export default faceService