import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json();
    
    // Call the simplified Python API
    const response = await callSimplePythonChat(message);
    
    return NextResponse.json({
      success: true,
      response: response
    });
    
  } catch (error) {
    console.error('Chat error:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to process your request'
    }, { status: 500 });
  }
}

function callSimplePythonChat(message: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const pythonPath = path.join(process.cwd(), 'simple_chat_api.py');
    const python = spawn('python3', [pythonPath, message]);
    
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