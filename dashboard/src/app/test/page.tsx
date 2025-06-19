'use client';

export default function TestPage() {
  return (
    <div>
      <h1>Test Page</h1>
      <p>API URL: {process.env.NEXT_PUBLIC_API_URL}</p>
      <p>API Key: {process.env.NEXT_PUBLIC_API_KEY ? 'Set' : 'Not set'}</p>
    </div>
  );
}