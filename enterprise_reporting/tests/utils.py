import os
import tempfile
from zipfile import ZipFile


def create_files(files_data):
    """
    Creates files based on provided file data.
    """
    files = []
    total_size = 0
    for file_data in files_data:
        tf = tempfile.NamedTemporaryFile(suffix='.txt')
        tf.write(file_data['size'] * b'i')
        tf.flush()
        tf.seek(0)

        files.append({
            'file': tf,
            'size': file_data['size'],
        })
        total_size += file_data['size']

    return files, total_size

def verify_compressed(self, delivery_files, files, original_file_size, password):
    """
    Verify that file is compress correctly.
    """
    # Verify file is compressed.
    zip_file_size = os.path.getsize(delivery_files)
    assert zip_file_size < original_file_size

    zipfile = ZipFile(delivery_files, 'r')

    for file in files:
        # Verify text file is present in zip file.
        assert file['file'].name.split('/')[-1] in zipfile.namelist()

        # Verify file content is readable with correct password.
        content = zipfile.read(file['file'].name.split('/')[-1], bytes(password, 'utf-8'))
        assert len(content) == file['size']

        # Also verify file is not accessible with any other passwords i.e wrong passwords.
        with self.assertRaises(RuntimeError):
            zipfile.read(file['file'].name.split('/')[-1], b'wrong-password')
