import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(request: NextRequest) {
  try {
    const { image } = await request.json();
    
    // Save base64 image to temporary file
    const imageBuffer = Buffer.from(image.split(',')[1], 'base64');
    const tempImagePath = path.join(process.cwd(), 'temp_image.png');
    fs.writeFileSync(tempImagePath, imageBuffer);
    
    // Call your Python image analysis
    const response = await callPythonImageAnalysis(tempImagePath);
    
    // Clean up temp file
    fs.unlinkSync(tempImagePath);
    
    return NextResponse.json({
      success: true,
      response: response
    });
    
  } catch (error) {
    console.error('Image analysis error:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to analyze image'
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