'use client';

import { useState } from 'react';
import { PageLayout } from '@/components/layout/page-layout';
import { useDocuments, useMentions, useAgents, useCreateDocument } from '@/lib/hooks/useApi';
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
  Plus
} from 'lucide-react';
import { DocumentType } from '@/lib/types';
import { format, formatDistanceToNow } from 'date-fns';

export default function CommunicationsPage() {
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [newDocumentTitle, setNewDocumentTitle] = useState('');
  const [newDocumentContent, setNewDocumentContent] = useState('');
  const [newDocumentType, setNewDocumentType] = useState<DocumentType>('update');
  
  const { data: documents, isLoading: documentsLoading } = useDocuments();
  const { data: agents, isLoading: agentsLoading } = useAgents();
  const { data: mentions, isLoading: mentionsLoading } = useMentions(selectedAgentId || 'all');
  const createDocumentMutation = useCreateDocument();

  // Calculate stats
  const totalDocuments = documents?.length || 0;
  const totalMentions = mentions?.length || 0;
  const recentDocuments = documents?.filter(doc => {
    const docTime = new Date(doc.created_at).getTime();
    const dayAgo = Date.now() - 24 * 60 * 60 * 1000;
    return docTime > dayAgo;
  }).length || 0;
  
  const unreadMentions = mentions?.filter(mention => !mention.read_at).length || 0;

  // Sort documents by creation date (newest first)
  const sortedDocuments = documents?.sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  ) || [];

  const sortedMentions = mentions?.sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  ) || [];

  const handleCreateDocument = () => {
    if (!newDocumentTitle.trim() || !newDocumentContent.trim() || !selectedAgentId) return;
    
    createDocumentMutation.mutate({
      type: newDocumentType,
      title: newDocumentTitle,
      content: newDocumentContent,
      author_id: selectedAgentId
    }, {
      onSuccess: () => {
        setNewDocumentTitle('');
        setNewDocumentContent('');
      }
    });
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
                                <Badge className={getDocumentTypeColor(doc.type)}>
                                  {doc.type}
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
                  value={selectedAgentId} 
                  onChange={(e) => setSelectedAgentId(e.target.value)}
                  className="px-3 py-2 border rounded-md"
                >
                  <option value="">All agents</option>
                  {agents?.map(agent => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name || agent.id} ({agent.role})
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
                    @mentions and notifications for {selectedAgentId || 'all agents'}
                  </CardDescription>
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
                          <Card key={mention.id} className={`p-4 ${mention.read_at ? 'opacity-60' : 'border-blue-200'}`}>
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1 space-y-1">
                                <div className="flex items-center gap-2">
                                  <Badge variant={mention.read_at ? "secondary" : "default"}>
                                    {mention.read_at ? "Read" : "Unread"}
                                  </Badge>
                                  <span className="text-sm text-muted-foreground">
                                    to @{mention.mentioned_agent_id}
                                  </span>
                                  <span className="text-sm text-muted-foreground">
                                    {formatDistanceToNow(new Date(mention.created_at), { addSuffix: true })}
                                  </span>
                                </div>
                                <p className="text-sm">
                                  Mentioned in: {mention.source_type} #{mention.source_id}
                                </p>
                                <p className="text-sm text-muted-foreground">
                                  {mention.context}
                                </p>
                              </div>
                            </div>
                          </Card>
                        ))
                      ) : (
                        <div className="text-center py-8">
                          <AtSign className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                          <p className="text-muted-foreground">No mentions found</p>
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
      </div>
    </PageLayout>
  );
}