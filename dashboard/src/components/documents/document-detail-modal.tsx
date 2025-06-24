'use client';

import { useState, useEffect } from 'react';
import { Document } from '@/lib/types';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { FileText, User, Calendar, AtSign } from 'lucide-react';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import { HeadlessPMClient } from '@/lib/api/client';

interface DocumentDetailModalProps {
  documentId: number | null;
  isOpen: boolean;
  onClose: () => void;
}

const getDocumentTypeColor = (type: string) => {
  switch (type) {
    case 'update': return 'bg-blue-100 text-blue-800';
    case 'question': return 'bg-yellow-100 text-yellow-800';
    case 'issue': return 'bg-red-100 text-red-800';
    case 'note': return 'bg-gray-100 text-gray-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

export function DocumentDetailModal({ documentId, isOpen, onClose }: DocumentDetailModalProps) {
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (documentId && isOpen) {
      setLoading(true);
      const client = new HeadlessPMClient();
      client.getDocument(documentId)
        .then(doc => {
          setDocument(doc);
        })
        .catch(err => {
          console.error('Failed to fetch document:', err);
          setDocument(null);
        })
        .finally(() => setLoading(false));
    }
  }, [documentId, isOpen]);

  if (!isOpen || !documentId) return null;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent 
        className="overflow-hidden flex flex-col"
        style={{
          width: '70vw',
          height: '85vh',
          maxWidth: '1200px',
          maxHeight: '85vh'
        }}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <FileText className="h-5 w-5" />
            Document Details
          </DialogTitle>
          {document && (
            <DialogDescription asChild>
              <div className="flex items-center gap-2 mt-2">
                <Badge className={getDocumentTypeColor(document.doc_type)}>
                  {document.doc_type}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Document #{document.id}
                </span>
              </div>
            </DialogDescription>
          )}
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="space-y-4">
              <div className="h-8 bg-gray-200 rounded animate-pulse" />
              <div className="h-32 bg-gray-200 rounded animate-pulse" />
            </div>
          ) : document ? (
            <div className="h-full flex flex-col space-y-4">
              {/* Title */}
              <div>
                <h2 className="text-xl font-semibold">{document.title}</h2>
              </div>

              {/* Metadata */}
              <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  <span>Author: @{document.author_id}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>{format(new Date(document.created_at), 'MMM dd, yyyy HH:mm')}</span>
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 min-h-0">
                <h3 className="text-sm font-medium text-muted-foreground mb-3">Content</h3>
                <div 
                  className="border rounded-lg bg-white"
                  style={{ height: 'calc(85vh - 250px)' }}
                >
                  <ScrollArea className="h-full">
                    <div className="p-6 max-w-none">
                      <div className="prose prose-base max-w-none prose-p:break-words prose-headings:break-words prose-code:break-all">
                      <ReactMarkdown 
                        children={String(document.content || '')}
                        components={{
                          // Proper code blocks with syntax highlighting appearance
                          code: ({node, inline, children, ...props}) => (
                            inline ? (
                              <code 
                                {...props} 
                                className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono break-all"
                              >
                                {children}
                              </code>
                            ) : (
                              <code {...props} className="block">
                                {children}
                              </code>
                            )
                          ),
                          pre: ({children, ...props}) => (
                            <div className="relative">
                              <pre 
                                {...props} 
                                className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono whitespace-pre"
                                style={{
                                  wordWrap: 'break-word',
                                  overflowWrap: 'break-word',
                                  whiteSpace: 'pre-wrap'
                                }}
                              >
                                {children}
                              </pre>
                            </div>
                          ),
                          // Ensure links are clickable and don't overflow
                          a: ({children, href, ...props}) => (
                            <a 
                              {...props} 
                              href={href}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 underline break-all"
                            >
                              {children}
                            </a>
                          ),
                          // Headers with proper spacing
                          h1: ({children, ...props}) => (
                            <h1 {...props} className="text-3xl font-bold mt-8 mb-6 break-words">
                              {children}
                            </h1>
                          ),
                          h2: ({children, ...props}) => (
                            <h2 {...props} className="text-2xl font-semibold mt-6 mb-4 break-words">
                              {children}
                            </h2>
                          ),
                          h3: ({children, ...props}) => (
                            <h3 {...props} className="text-xl font-medium mt-5 mb-3 break-words">
                              {children}
                            </h3>
                          ),
                          // Paragraphs with proper spacing
                          p: ({children, ...props}) => (
                            <p {...props} className="mb-6 leading-relaxed break-words text-base">
                              {children}
                            </p>
                          ),
                          // Lists
                          ul: ({children, ...props}) => (
                            <ul {...props} className="list-disc list-inside mb-4 space-y-1">
                              {children}
                            </ul>
                          ),
                          ol: ({children, ...props}) => (
                            <ol {...props} className="list-decimal list-inside mb-4 space-y-1">
                              {children}
                            </ol>
                          ),
                          li: ({children, ...props}) => (
                            <li {...props} className="break-words">
                              {children}
                            </li>
                          ),
                          // Blockquotes
                          blockquote: ({children, ...props}) => (
                            <blockquote {...props} className="border-l-4 border-gray-300 pl-4 italic my-4 break-words">
                              {children}
                            </blockquote>
                          ),
                          // Tables
                          table: ({children, ...props}) => (
                            <div className="overflow-x-auto mb-4">
                              <table {...props} className="min-w-full border-collapse border border-gray-300">
                                {children}
                              </table>
                            </div>
                          ),
                          th: ({children, ...props}) => (
                            <th {...props} className="border border-gray-300 px-3 py-2 bg-gray-100 font-semibold text-left">
                              {children}
                            </th>
                          ),
                          td: ({children, ...props}) => (
                            <td {...props} className="border border-gray-300 px-3 py-2 break-words">
                              {children}
                            </td>
                          ),
                          // Images
                          img: ({src, alt, ...props}) => (
                            <img 
                              {...props} 
                              src={src} 
                              alt={alt} 
                              className="max-w-full h-auto rounded-lg my-4"
                            />
                          )
                        }}
                      />
                      
                      {/* Mentions */}
                      {String(document.content || '').includes('@') && (
                        <div className="mt-6 space-y-2">
                          <div className="flex items-center gap-2 text-sm font-medium">
                            <AtSign className="h-4 w-4" />
                            <span>Mentions in this document:</span>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {String(document.content || '').match(/@\w+/g)?.map((mention, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {mention}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      </div>
                    </div>
                  </ScrollArea>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground">Document not found</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}