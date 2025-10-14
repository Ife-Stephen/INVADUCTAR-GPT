import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('image') as File;
    
    if (!file) {
      return NextResponse.json({
        success: false,
        error: 'No image file provided'
      }, { status: 400 });
    }

    // Save the uploaded file temporarily
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    
    // Create uploads directory if it doesn't exist
    const uploadsDir = path.join(process.cwd(), 'uploads');
    if (!fs.existsSync(uploadsDir)) {
      fs.mkdirSync(uploadsDir, { recursive: true });
    }
    
    const filename = `${Date.now()}_${file.name}`;
    const filepath = path.join(uploadsDir, filename);
    
    fs.writeFileSync(filepath, buffer);

    // Call the Python image analysis API
    const response = await callPythonImageAnalysis(filepath);
    
    // Clean up the temporary file
    fs.unlinkSync(filepath);

    return NextResponse.json({
      success: true,
      response: response
    });
    
  } catch (error) {
    console.error('Image analysis error:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to analyze the image'
    }, { status: 500 });
  }
}

function callPythonImageAnalysis(imagePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const pythonPath = path.join(process.cwd(), 'image_api.py');
    const python = spawn('python3', [pythonPath, imagePath]);
    
    let output = '';
    let error = '';
    
    python.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    python.stderr.on('data', (data) => {
      error += data.toString();
    });
    
    python.on('close', (code) => {
      if (code === 0) {
        resolve(output.trim());
      } else {
        reject(new Error(`Python process failed: ${error}`));
      }
    });
    
    python.on('error', (err) => {
      reject(err);
    });
  });
}