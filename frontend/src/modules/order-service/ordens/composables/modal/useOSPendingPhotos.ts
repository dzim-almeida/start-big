import { ref, type ComputedRef } from 'vue';

import type { PendingPhoto } from '../../components/form/OSFotoGallery.vue';

interface UploadPhotoRequest {
  osNumber: string;
  imageFile: File;
}

interface UseOSPendingPhotosParams {
  osNumber: ComputedRef<string | null>;
  uploadPhoto: (payload: UploadPhotoRequest) => Promise<unknown>;
}

export function useOSPendingPhotos({
  osNumber,
  uploadPhoto,
}: UseOSPendingPhotosParams) {
  const pendingPhotos = ref<PendingPhoto[]>([]);

  function handleAddPhoto(file: File) {
    pendingPhotos.value.push({
      file,
      previewUrl: URL.createObjectURL(file),
      nome_arquivo: file.name,
    });
  }

  function handleRemovePending(index: number) {
    const target = pendingPhotos.value[index];
    if (!target) return;

    URL.revokeObjectURL(target.previewUrl);
    pendingPhotos.value.splice(index, 1);
  }

  function clearPendingPhotos() {
    pendingPhotos.value.forEach(photo => URL.revokeObjectURL(photo.previewUrl));
    pendingPhotos.value = [];
  }

  async function uploadPendingPhotos() {
    const currentOsNumber = osNumber.value;
    if (!currentOsNumber || pendingPhotos.value.length === 0) return;

    for (const photo of pendingPhotos.value) {
      await uploadPhoto({
        osNumber: currentOsNumber,
        imageFile: photo.file,
      });
    }

    clearPendingPhotos();
  }

  return {
    pendingPhotos,
    handleAddPhoto,
    handleRemovePending,
    clearPendingPhotos,
    uploadPendingPhotos,
  };
}
