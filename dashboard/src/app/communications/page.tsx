'use client';

import { useState, useEffect } from 'react';
import { PageLayout } from '@/components/layout/page-layout';
import { useDocuments, useMentions, useMentionsByRole, useAgents, useCreateDocument } from '@/lib/hooks/useApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { StatsWidget } from '@/components/ui/stats-widget';
import { 
  MessageSquare, 
  AtSign, 
  FileText, 
  Users, 
  Clock,
  Send,
  Plus,
  ExternalLink
} from 'lucide-react';
import { DocumentType } from '@/lib/types';
import { format, formatDistanceToNow } from 'date-fns';
import { DocumentDetailModal } from '@/components/documents/document-detail-modal';

export default function CommunicationsPage() {
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [newDocumentTitle, setNewDocumentTitle] = useState('');
  const [newDocumentContent, setNewDocumentContent] = useState('');
  const [newDocumentType, setNewDocumentType] = useState<DocumentType>('update');
  const [isBroadcast, setIsBroadcast] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [isDocumentModalOpen, setIsDocumentModalOpen] = useState(false);
  const [documentSearch, setDocumentSearch] = useState('');
  const [mentionSearch, setMentionSearch] = useState('');
  
  const { data: documents, isLoading: documentsLoading } = useDocuments();
  const { data: agents, isLoading: agentsLoading } = useAgents();
  const { data: mentions, isLoading: mentionsLoading } = useMentionsByRole(selectedRole || undefined, false); // Use role-based filtering
  const createDocumentMutation = useCreateDocument();
  
  // Get unique roles from agents
  const roles = [...new Set(agents?.map(agent => agent.role) || [])];

  // Calculate stats
  const totalDocuments = documents?.length || 0;
  const totalMentions = mentions?.length || 0;
  const recentDocuments = documents?.filter(doc => {
    const docTime = new Date(doc.created_at).getTime();
    const dayAgo = Date.now() - 24 * 60 * 60 * 1000;
    return docTime > dayAgo;
  }).length || 0;
  
  const unreadMentions = mentions?.filter(mention => !mention.is_read).length || 0;

  // Debug logging
  console.log('Documents:', documents?.length, documents);
  console.log('Mentions:', mentions?.length, mentions);
  console.log('Selected Role:', selectedRole);

  // Filter and sort documents
  const filteredDocuments = documents?.filter(doc => {
    if (!documentSearch) return true;
    const searchLower = documentSearch.toLowerCase();
    return doc.title.toLowerCase().includes(searchLower) || 
           doc.content.toLowerCase().includes(searchLower) ||
           doc.author_id.toLowerCase().includes(searchLower);
  }) || [];

  const sortedDocuments = filteredDocuments.sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  // Filter and sort mentions
  const filteredMentions = mentions?.filter(mention => {
    if (!mentionSearch) return true;
    const searchLower = mentionSearch.toLowerCase();
    return mention.mentioned_agent_id.toLowerCase().includes(searchLower) ||
           mention.created_by.toLowerCase().includes(searchLower) ||
           (mention.document_title && mention.document_title.toLowerCase().includes(searchLower)) ||
           (mention.task_title && mention.task_title.toLowerCase().includes(searchLower));
  }) || [];

  const sortedMentions = filteredMentions.sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const handleCreateDocument = () => {
    if (!newDocumentTitle.trim() || !newDocumentContent.trim() || !selectedAgentId) return;
    
    let finalContent = newDocumentContent;
    
    // If broadcast is selected, add @mentions for all agents
    if (isBroadcast && agents) {
      const mentionTags = agents
        .filter(agent => agent.agent_id !== selectedAgentId) // Don't mention self
        .map(agent => `@${agent.agent_id}`)
        .join(' ');
      
      if (mentionTags) {
        finalContent = `${newDocumentContent}\n\n${mentionTags}`;
      }
    }
    
    createDocumentMutation.mutate({
      type: newDocumentType,
      title: newDocumentTitle,
      content: finalContent,
      author_id: selectedAgentId
    }, {
      onSuccess: () => {
        setNewDocumentTitle('');
        setNewDocumentContent('');
        setIsBroadcast(false);
      }
    });
  };

  const handleOpenDocument = (documentId: number) => {
    setSelectedDocumentId(documentId);
    setIsDocumentModalOpen(true);
  };

  const getDocumentTypeColor = (type: DocumentType) => {
    switch (type) {
      case 'update': return 'bg-blue-100 text-blue-800';
      case 'question': return 'bg-yellow-100 text-yellow-800';
      case 'issue': return 'bg-red-100 text-red-800';
      case 'note': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <PageLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Communications</h1>
          <p className="text-muted-foreground mt-1">
            Team documents, mentions, and collaboration
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsWidget
            title="Total Documents"
            value={totalDocuments}
            description={`${recentDocuments} created today`}
            icon={<FileText className="h-4 w-4" />}
          />
          <StatsWidget
            title="Active Mentions"
            value={totalMentions}
            description={`${unreadMentions} unread`}
            icon={<AtSign className="h-4 w-4" />}
          />
          <StatsWidget
            title="Team Members"
            value={agents?.length || 0}
            description="Registered agents"
            icon={<Users className="h-4 w-4" />}
          />
          <StatsWidget
            title="Recent Activity"
            value={recentDocuments}
            description="Documents today"
            icon={<Clock className="h-4 w-4" />}
          />
        </div>

        {/* Main Content */}
        <Tabs defaultValue="documents" className="space-y-4">
          <TabsList>
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="mentions">Mentions</TabsTrigger>
            <TabsTrigger value="create">Create Document</TabsTrigger>
          </TabsList>

          <TabsContent value="documents" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Document Timeline
                </CardTitle>
                <CardDescription>
                  Latest team communications and updates
                </CardDescription>
                <div className="mt-4">
                  <Input
                    placeholder="Search documents by title, content, or author..."
                    value={documentSearch}
                    onChange={(e) => setDocumentSearch(e.target.value)}
                    className="max-w-md"
                  />
                </div>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px]">
                  <div className="space-y-4">
                    {documentsLoading ? (
                      Array.from({ length: 5 }).map((_, i) => (
                        <Skeleton key={i} className="h-24" />
                      ))
                    ) : sortedDocuments.length > 0 ? (
                      sortedDocuments.map((doc) => (
                        <Card key={doc.id} className="p-4">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center gap-2">
                                <Badge className={getDocumentTypeColor(doc.doc_type)}>
                                  {doc.doc_type}
                                </Badge>
                                <span className="text-sm text-muted-foreground">
                                  by {doc.author_id}
                                </span>
                                <span className="text-sm text-muted-foreground">
                                  {formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}
                                </span>
                              </div>
                              <h3 className="font-medium">{doc.title}</h3>
                              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                                {doc.content}
                              </p>
                            </div>
                          </div>
                        </Card>
                      ))
                    ) : (
                      <div className="text-center py-8">
                        <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                        <p className="text-muted-foreground">No documents found</p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="mentions" className="space-y-4">
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <select 
                  value={selectedRole} 
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="px-3 py-2 border rounded-md"
                >
                  <option value="">All roles</option>
                  {roles.map(role => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AtSign className="h-5 w-5" />
                    Mentions Timeline
                  </CardTitle>
                  <CardDescription>
                    @mentions and notifications for {selectedRole || 'all roles'} 
                    {mentions && ` (${mentions.length} total, ${unreadMentions} unread)`}
                  </CardDescription>
                  <div className="mt-4">
                    <Input
                      placeholder="Search mentions by agent, document, or task..."
                      value={mentionSearch}
                      onChange={(e) => setMentionSearch(e.target.value)}
                      className="max-w-md"
                    />
                  </div>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[500px]">
                    <div className="space-y-4">
                      {mentionsLoading ? (
                        Array.from({ length: 3 }).map((_, i) => (
                          <Skeleton key={i} className="h-20" />
                        ))
                      ) : sortedMentions.length > 0 ? (
                        sortedMentions.map((mention) => (
                          <Card key={mention.id} className={`p-4 ${mention.is_read ? 'opacity-60' : 'border-blue-200'}`}>
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1 space-y-1">
                                <div className="flex items-center gap-2">
                                  <Badge variant={mention.is_read ? "secondary" : "default"}>
                                    {mention.is_read ? "Read" : "Unread"}
                                  </Badge>
                                  <span className="text-sm text-muted-foreground">
                                    from @{mention.created_by}
                                  </span>
                                  <span className="text-sm text-muted-foreground">
                                    {formatDistanceToNow(new Date(mention.created_at), { addSuffix: true })}
                                  </span>
                                </div>
                                {mention.document_id && (
                                  <div className="flex items-center gap-2">
                                    <p className="text-sm">
                                      Mentioned in document: 
                                    </p>
                                    <Button
                                      variant="link"
                                      size="sm"
                                      className="p-0 h-auto text-blue-600 hover:text-blue-800"
                                      onClick={() => handleOpenDocument(mention.document_id!)}
                                    >
                                      <ExternalLink className="h-3 w-3 mr-1" />
                                      {mention.document_title || `Document #${mention.document_id}`}
                                    </Button>
                                  </div>
                                )}
                                {mention.task_id && (
                                  <p className="text-sm">
                                    Mentioned in task: {mention.task_title || `Task #${mention.task_id}`}
                                  </p>
                                )}
                              </div>
                            </div>
                          </Card>
                        ))
                      ) : (
                        <div className="text-center py-8">
                          <AtSign className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                          <p className="text-muted-foreground">
                            {selectedRole ? `No mentions found for ${selectedRole} role` : 'No mentions found'}
                          </p>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="create" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plus className="h-5 w-5" />
                  Create New Document
                </CardTitle>
                <CardDescription>
                  Share updates, ask questions, or document issues with your team
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Author</label>
                    <select 
                      value={selectedAgentId} 
                      onChange={(e) => setSelectedAgentId(e.target.value)}
                      className="w-full px-3 py-2 border rounded-md mt-1"
                    >
                      <option value="">Select author...</option>
                      {agents?.map(agent => (
                        <option key={agent.id} value={agent.id}>
                          {agent.name || agent.id} ({agent.role})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Type</label>
                    <select 
                      value={newDocumentType} 
                      onChange={(e) => setNewDocumentType(e.target.value as DocumentType)}
                      className="w-full px-3 py-2 border rounded-md mt-1"
                    >
                      <option value="update">Update</option>
                      <option value="question">Question</option>
                      <option value="issue">Issue</option>
                      <option value="note">Note</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium">Title</label>
                  <Input
                    value={newDocumentTitle}
                    onChange={(e) => setNewDocumentTitle(e.target.value)}
                    placeholder="Document title..."
                    className="mt-1"
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium">Content</label>
                  <textarea
                    value={newDocumentContent}
                    onChange={(e) => setNewDocumentContent(e.target.value)}
                    placeholder="Write your message here... Use @username to mention team members"
                    className="w-full px-3 py-2 border rounded-md mt-1 min-h-[120px] resize-none"
                  />
                </div>
                
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="broadcast"
                    checked={isBroadcast}
                    onChange={(e) => setIsBroadcast(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="broadcast" className="text-sm font-medium">
                    📢 Broadcast to all agents
                  </label>
                  <span className="text-xs text-muted-foreground">
                    (Automatically adds @mentions for all team members)
                  </span>
                </div>
                
                <Button 
                  onClick={handleCreateDocument}
                  disabled={!newDocumentTitle.trim() || !newDocumentContent.trim() || !selectedAgentId || createDocumentMutation.isPending}
                  className="w-full"
                >
                  {createDocumentMutation.isPending ? (
                    "Creating..."
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Create Document
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <DocumentDetailModal
          documentId={selectedDocumentId}
          isOpen={isDocumentModalOpen}
          onClose={() => {
            setIsDocumentModalOpen(false);
            setSelectedDocumentId(null);
          }}
        />
      </div>
    </PageLayout>
  );
}