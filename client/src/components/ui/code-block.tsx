import React from "react";
import { cn } from "@/lib/utils";
import { Copy } from "lucide-react";
import { Button } from "./button";
import { useToast } from "@/hooks/use-toast";

interface CodeBlockProps {
  code: string;
  language?: "sql" | "json" | "text";
  className?: string;
  showCopyButton?: boolean;
}

function formatSqlCode(sqlCode: string): string {
  if (!sqlCode) return "";
  
  // Define SQL keywords for syntax highlighting
  const keywords = [
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", 
    "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "OFFSET", "INSERT INTO", "VALUES",
    "UPDATE", "SET", "DELETE", "CREATE", "ALTER", "DROP", "TABLE", "VIEW", "INDEX",
    "CONSTRAINT", "PRIMARY KEY", "FOREIGN KEY", "AS", "ON", "AND", "OR", "NOT", "IN",
    "BETWEEN", "LIKE", "IS NULL", "IS NOT NULL", "DISTINCT", "UNION", "ALL", "CASE",
    "WHEN", "THEN", "ELSE", "END"
  ];
  
  // Define SQL functions
  const functions = [
    "SUM", "COUNT", "AVG", "MIN", "MAX", "SUBSTRING", "CONCAT", "UPPER", "LOWER",
    "DATE", "DATETIME", "TRIM", "ROUND", "CAST", "COALESCE"
  ];
  
  // Apply syntax highlighting classes
  let highlightedCode = sqlCode;
  
  // Apply keyword highlighting
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
    highlightedCode = highlightedCode.replace(regex, match => 
      `<span class="sql-keyword">${match}</span>`
    );
  });
  
  // Apply function highlighting
  functions.forEach(func => {
    const regex = new RegExp(`\\b${func}\\b\\(`, 'gi');
    highlightedCode = highlightedCode.replace(regex, match => 
      `<span class="sql-function">${match.substring(0, match.length - 1)}</span>(`
    );
  });
  
  // Highlight table names (simplified approach)
  highlightedCode = highlightedCode.replace(/\b(\w+)\b\./g, match => 
    `<span class="sql-table">${match.substring(0, match.length - 1)}</span>.`
  );
  
  // Highlight strings
  highlightedCode = highlightedCode.replace(/'[^']*'/g, match => 
    `<span class="sql-string">${match}</span>`
  );
  
  // Highlight numbers
  highlightedCode = highlightedCode.replace(/\b\d+\b/g, match => 
    `<span class="sql-number">${match}</span>`
  );
  
  return highlightedCode;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = "sql",
  className,
  showCopyButton = true,
}) => {
  const { toast } = useToast();
  
  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    toast({
      description: "Code copied to clipboard",
    });
  };
  
  const formattedCode = language === "sql" ? formatSqlCode(code) : code;
  
  return (
    <div className={cn("relative rounded-md bg-gray-50 font-mono text-sm", className)}>
      {showCopyButton && (
        <div className="absolute right-2 top-2">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={handleCopy} 
            className="h-8 w-8 rounded-md hover:bg-gray-200"
          >
            <Copy className="h-4 w-4" />
            <span className="sr-only">Copy code</span>
          </Button>
        </div>
      )}
      <pre className="overflow-x-auto p-4">
        <code dangerouslySetInnerHTML={{ __html: formattedCode }} />
      </pre>
    </div>
  );
};
