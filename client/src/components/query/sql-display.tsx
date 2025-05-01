import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Edit, Copy, Save } from "lucide-react";
import { CodeBlock } from "@/components/ui/code-block";
import { useToast } from "@/hooks/use-toast";
import { useQueryActions } from "@/hooks/use-query";

interface SqlDisplayProps {
  sql: string;
  queryId?: number;
  isSaved?: boolean;
}

export default function SqlDisplay({ sql, queryId, isSaved = false }: SqlDisplayProps) {
  const { toast } = useToast();
  const { saveQuery, unsaveQuery, isSaving, isUnsaving } = useQueryActions();
  
  if (!sql) {
    return null;
  }
  
  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    toast({
      description: "SQL copied to clipboard",
    });
  };
  
  const handleSaveToggle = () => {
    if (!queryId) return;
    
    if (isSaved) {
      unsaveQuery(queryId);
    } else {
      saveQuery(queryId);
    }
  };
  
  return (
    <Card className="mb-6">
      <CardHeader className="flex flex-row items-center justify-between px-6 py-4">
        <div>
          <CardTitle className="text-lg text-gray-900">Generated SQL Query</CardTitle>
          <CardDescription className="mt-1 text-sm text-gray-500">
            Converted from your natural language question
          </CardDescription>
        </div>
        <div className="flex space-x-2">
          <Button 
            variant="outline" 
            size="sm" 
            className="text-xs"
          >
            <Edit className="h-3.5 w-3.5 mr-1" />
            Edit
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            className="text-xs"
            onClick={handleCopy}
          >
            <Copy className="h-3.5 w-3.5 mr-1" />
            Copy
          </Button>
          {queryId && (
            <Button 
              variant="outline" 
              size="sm" 
              className="text-xs"
              onClick={handleSaveToggle}
              disabled={isSaving || isUnsaving}
            >
              <Save className="h-3.5 w-3.5 mr-1" />
              {isSaved ? "Unsave" : "Save"}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-4 bg-gray-50">
        <CodeBlock code={sql} language="sql" className="w-full" showCopyButton={false} />
      </CardContent>
    </Card>
  );
}
