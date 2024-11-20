const unzipper = require('unzipper');
const fs = require('fs');
const path = require('path');
const PDFDocument = require('pdfkit');
const sizeOf = require('image-size');

// Definir la ruta absoluta para la carpeta "temp" y "output_pdfs"
const rootDir = path.resolve(__dirname, '..'); // Ruta raíz del proyecto
const tempFolderPath = path.join(rootDir, 'temp'); // Carpeta temp donde se descargan los ZIP
const outputPDFDir = path.join(tempFolderPath, 'output_pdfs'); // Carpeta output_pdfs dentro de temp
const tempExtractedDir = path.join(tempFolderPath, 'temp_extracted'); // Carpeta temp_extracted dentro de temp

console.log(`Recibido: ZIP = ${process.argv[2]}, Serie = ${process.argv[3]}, Capítulo = ${process.argv[4]}`);

// Función para extraer el ZIP a un directorio temporal con manejo de errores y log de archivos extraídos
async function extractZip(zipPath, extractTo) {
    try {
        const directory = await unzipper.Open.file(zipPath);
        console.log(`Extrayendo el ZIP: ${zipPath} a ${extractTo}`);
        await directory.extract({ path: extractTo, concurrency: 5 });
        
        // Mostrar los archivos extraídos
        console.log('Archivos extraídos:');
        directory.files.forEach(file => console.log(file.path));

        console.log(`Archivo ZIP extraído correctamente en ${extractTo}`);
    } catch (error) {
        console.error(`Error al extraer el archivo ZIP: ${error.message}`);
        throw error;
    }
}

// Función para obtener todos los archivos de imagen en un directorio
function getImageFiles(directory) {
    try {
        return fs.readdirSync(directory, { withFileTypes: true })
            .filter(dirent => dirent.isFile())
            .filter(file => {
                const ext = path.extname(file.name).toLowerCase();
                return ext === '.jpg' || ext === '.jpeg' || ext === '.png';
            })
            .map(file => path.join(directory, file.name));
    } catch (error) {
        console.error(`Error al leer el directorio de imágenes: ${error.message}`);
        return [];
    }
}

// Función para convertir imágenes en PDF usando PDFKit
function imagesToPDF(imagePaths, outputPDFPath) {
    return new Promise((resolve, reject) => {
        const doc = new PDFDocument({ autoFirstPage: false });
        const stream = fs.createWriteStream(outputPDFPath);
        doc.pipe(stream);

        imagePaths.forEach(imagePath => {
            try {
                const dimensions = sizeOf(imagePath);
                if (!dimensions) {
                    throw new Error(`Error al obtener dimensiones de la imagen: ${imagePath}`);
                }

                doc.addPage({ size: [dimensions.width, dimensions.height] });
                doc.image(imagePath, 0, 0, { width: dimensions.width, height: dimensions.height });
            } catch (error) {
                console.error(`Error al procesar la imagen ${imagePath}: ${error.message}`);
            }
        });

        doc.end();

        stream.on('finish', () => {
            resolve(outputPDFPath);
        });

        stream.on('error', (error) => {
            console.error(`Error al escribir el archivo PDF: ${error.message}`);
            reject(error);
        });
    });
}

// Función para procesar un solo archivo ZIP y generar los PDFs
async function processSingleZip(zipFilePath, outputDir, serie, chapter) {
    // Usar la carpeta temp_extracted dentro de temp
    await extractZip(zipFilePath, tempExtractedDir);

    const images = getImageFiles(tempExtractedDir);
    if (images.length > 0) {
        const outputPDFPath = path.join(outputDir, `${serie}_${chapter}.pdf`);
        await imagesToPDF(images, outputPDFPath);
        console.log(`PDF creado en ${outputPDFPath}`);
    } else {
        console.log(`No se encontraron imágenes en el ZIP: ${zipFilePath}`);
    }

    // Eliminar los archivos temporales extraídos
    try {
        fs.rmSync(tempExtractedDir, { recursive: true, force: true });
        console.log(`Carpeta temporal eliminada: ${tempExtractedDir}`);
    } catch (error) {
        console.error(`Error al eliminar la carpeta temporal: ${error.message}`);
    }
}

// Función para procesar todos los ZIPs en la carpeta "temp" y generar los PDFs en "output_pdfs"
async function processZipsInTempFolder(serie, chapter) {
    if (!fs.existsSync(outputPDFDir)) {
        fs.mkdirSync(outputPDFDir, { recursive: true });
        console.log(`Directorio de salida creado: ${outputPDFDir}`);
    }

    const zipFiles = fs.readdirSync(tempFolderPath).filter(file => path.extname(file) === '.zip');

    if (zipFiles.length === 0) {
        console.log(`No se encontraron archivos ZIP en la carpeta "temp".`);
        return;
    }

    for (const zipFile of zipFiles) {
        const zipFilePath = path.join(tempFolderPath, zipFile);
        await processSingleZip(zipFilePath, outputPDFDir, serie, chapter);

        try {
            fs.unlinkSync(zipFilePath); // Eliminar el ZIP después de procesarlo
            console.log(`Archivo ZIP eliminado: ${zipFilePath}`);
        } catch (error) {
            console.error(`Error al eliminar el archivo ZIP: ${error.message}`);
        }
    }

    console.log('Todos los ZIPs han sido procesados.');
}

// Función para eliminar un archivo con un pequeño retraso
function deleteFileWithDelay(filePath, delay = 500) {
    setTimeout(() => {
        try {
            fs.unlinkSync(filePath);
            console.log(`Archivo ${filePath} eliminado correctamente.`);
        } catch (error) {
            console.error(`Error al eliminar el archivo ${filePath}: ${error.message}`);
        }
    }, delay);
}

// Obtener los argumentos de la línea de comandos (serie y capítulo)
const zipFilePath = process.argv[2]; // Ruta del archivo ZIP
const serie = process.argv[3];       // Nombre de la serie
const chapter = process.argv[4];     // Número del capítulo

if (!zipFilePath || !serie || !chapter) {
    console.error("Faltan argumentos: ZIP, Serie o Capítulo.");
    process.exit(1);
}

processZipsInTempFolder(serie, chapter)
    .catch(err => console.error('Error:', err));

