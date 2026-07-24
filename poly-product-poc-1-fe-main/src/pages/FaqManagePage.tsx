import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Search, Edit2, Trash2, Upload, FileText, X, Loader2 } from 'lucide-react';
import { 
  useFaqs, 
  useSections, 
  useFilteredFaqs, 
  useCreateFaq, 
  useUpdateFaq, 
  useDeleteFaq,
  useIngestPdf 
} from '@/hooks/useFaqApi';
import { AppLayout } from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { TableSkeleton } from '@/components/ui/skeleton-loaders';
import { ErrorState } from '@/components/ui/error-state';
import { FAQ } from '@/types/faq';
import { format } from 'date-fns';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';

const FaqManagePage = () => {
  const { data: faqs, isLoading, isError, refetch } = useFaqs();
  const sections = useSections(faqs);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const filteredFaqs = useFilteredFaqs(faqs, searchQuery, selectedSection);

  const createMutation = useCreateFaq();
  const updateMutation = useUpdateFaq();
  const deleteMutation = useDeleteFaq();
  const { mutate: ingestPdf, isPending: isIngesting, progress } = useIngestPdf();

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [editingFaq, setEditingFaq] = useState<FAQ | null>(null);
  const [formData, setFormData] = useState({
    section: '',
    question: '',
    answer: '',
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const resetForm = () => {
    setFormData({ section: '', question: '', answer: '' });
    setEditingFaq(null);
  };

  const openCreateDialog = () => {
    resetForm();
    setIsDialogOpen(true);
  };

  const openEditDialog = (faq: FAQ) => {
    setEditingFaq(faq);
    setFormData({
      section: faq.section,
      question: faq.question,
      answer: faq.answer,
    });
    setIsDialogOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.section || !formData.question || !formData.answer) {
      return;
    }

    if (editingFaq) {
      updateMutation.mutate(
        { id: editingFaq.id, data: formData },
        { onSuccess: () => { setIsDialogOpen(false); resetForm(); } }
      );
    } else {
      createMutation.mutate(formData, {
        onSuccess: () => { setIsDialogOpen(false); resetForm(); }
      });
    }
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      ingestPdf(selectedFile, {
        onSuccess: () => {
          setIsUploadDialogOpen(false);
          setSelectedFile(null);
        }
      });
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto">
        {/* Page Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8"
        >
          <div>
            <h1 className="text-3xl font-bold text-foreground">
              Manage FAQs
            </h1>
            <p className="text-muted-foreground mt-1">
              Create, edit, and organize your knowledge base
            </p>
          </div>
          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={() => setIsUploadDialogOpen(true)}
              disabled={isIngesting}
            >
              <Upload className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">Import PDF</span>
            </Button>
            <Button variant="brand" size="lg" onClick={openCreateDialog}>
              <Plus className="w-4 h-4" />
              Add FAQ
            </Button>
          </div>
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex flex-col sm:flex-row gap-4 mb-6"
        >
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search FAQs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select
            value={selectedSection || 'all'}
            onValueChange={(value) => setSelectedSection(value === 'all' ? null : value)}
          >
            <SelectTrigger className="w-full sm:w-48">
              <SelectValue placeholder="All Sections" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sections</SelectItem>
              {sections.map((section) => (
                <SelectItem key={section.id} value={section.name}>
                  {section.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </motion.div>

        {/* Error State */}
        {isError && (
          <ErrorState 
            title="Failed to load FAQs"
            message="We couldn't fetch your FAQs. Please check your connection and try again."
            onRetry={() => refetch()}
          />
        )}

        {/* FAQ Table */}
        {!isError && (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Question
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden md:table-cell">
                      Section
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden lg:table-cell">
                      Updated
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {isLoading ? (
                    <TableSkeleton count={5} />
                  ) : (
                    <AnimatePresence mode="popLayout">
                      {filteredFaqs.map((faq, index) => (
                        <motion.tr
                          key={faq.id}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.2, delay: index * 0.02 }}
                          className="hover:bg-muted/30 transition-colors"
                        >
                          <td className="px-6 py-4">
                            <p className="font-medium text-foreground line-clamp-1">
                              {faq.question}
                            </p>
                            <p className="text-sm text-muted-foreground line-clamp-1 mt-0.5">
                              {faq.answer}
                            </p>
                          </td>
                          <td className="px-6 py-4 hidden md:table-cell">
                            <span className="inline-flex px-2.5 py-1 rounded-full text-xs font-medium bg-accent text-accent-foreground">
                              {faq.section}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-muted-foreground hidden lg:table-cell">
                            {format(faq.updatedAt, 'MMM d, yyyy')}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => openEditDialog(faq)}
                                className="hover:bg-accent"
                                disabled={updateMutation.isPending}
                              >
                                <Edit2 className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDelete(faq.id)}
                                className="hover:bg-destructive/10 hover:text-destructive"
                                disabled={deleteMutation.isPending}
                              >
                                {deleteMutation.isPending ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Trash2 className="w-4 h-4" />
                                )}
                              </Button>
                            </div>
                          </td>
                        </motion.tr>
                      ))}
                    </AnimatePresence>
                  )}
                </tbody>
              </table>
            </div>

            {!isLoading && filteredFaqs.length === 0 && (
              <div className="py-12 text-center text-muted-foreground">
                <p>No FAQs found. Create your first FAQ to get started.</p>
              </div>
            )}
          </Card>
        )}

        {/* Create/Edit Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>
                {editingFaq ? 'Edit FAQ' : 'Create New FAQ'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="section">Section</Label>
                <Input
                  id="section"
                  placeholder="e.g., Getting Started"
                  value={formData.section}
                  onChange={(e) => setFormData({ ...formData, section: e.target.value })}
                  list="sections-list"
                  disabled={isSubmitting}
                />
                <datalist id="sections-list">
                  {sections.map((s) => (
                    <option key={s.id} value={s.name} />
                  ))}
                </datalist>
              </div>

              <div className="space-y-2">
                <Label htmlFor="question">Question</Label>
                <Input
                  id="question"
                  placeholder="What would you like to answer?"
                  value={formData.question}
                  onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                  disabled={isSubmitting}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="answer">Answer</Label>
                <Textarea
                  id="answer"
                  placeholder="Provide a clear and helpful answer..."
                  rows={4}
                  value={formData.answer}
                  onChange={(e) => setFormData({ ...formData, answer: e.target.value })}
                  disabled={isSubmitting}
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsDialogOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="brand" disabled={isSubmitting}>
                  {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  {editingFaq ? 'Save Changes' : 'Create FAQ'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* PDF Upload Dialog */}
        <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Import FAQs from PDF</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div 
                className="border-2 border-dashed border-border rounded-xl p-8 text-center hover:border-primary/50 transition-colors cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={handleFileSelect}
                  disabled={isIngesting}
                />
                {selectedFile ? (
                  <div className="flex items-center justify-center gap-3">
                    <FileText className="w-8 h-8 text-primary" />
                    <div className="text-left">
                      <p className="font-medium text-foreground">{selectedFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <Upload className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
                    <p className="text-foreground font-medium">Click to upload PDF</p>
                    <p className="text-sm text-muted-foreground mt-1">or drag and drop</p>
                  </>
                )}
              </div>

              {isIngesting && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Uploading...</span>
                    <span className="text-foreground font-medium">{progress}%</span>
                  </div>
                  <Progress value={progress} className="h-2" />
                </div>
              )}

              <div className="flex justify-end gap-3">
                <Button
                  variant="ghost"
                  onClick={() => { setIsUploadDialogOpen(false); setSelectedFile(null); }}
                  disabled={isIngesting}
                >
                  Cancel
                </Button>
                <Button 
                  variant="brand" 
                  onClick={handleUpload}
                  disabled={!selectedFile || isIngesting}
                >
                  {isIngesting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Upload & Process
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </AppLayout>
  );
};

export default FaqManagePage;
