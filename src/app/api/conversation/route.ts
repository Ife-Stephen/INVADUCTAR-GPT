import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const conversationPath = path.join(process.cwd(), 'conversation.json');
    
    if (!fs.existsSync(conversationPath)) {
      return NextResponse.json({
        success: true,
        messages: []
      });
    }
    
    const conversationData = fs.readFileSync(conversationPath, 'utf-8');
    const conversation = JSON.parse(conversationData);
    
    const messages = conversation
      .filter((msg: any) => msg.content && msg.content.trim()) // Filter out empty content
      .map((msg: any, index: number) => ({
        id: index + 1,
        message: msg.content,
        isUser: msg.type === 'human',
        timestamp: new Date().toISOString()
      }));
    
    return NextResponse.json({
      success: true,
      messages: messages
    });
    
  } catch (error) {
    console.error('Failed to load conversation:', error);
    return NextResponse.json({
      success: true,
      messages: []
    });
  }
}