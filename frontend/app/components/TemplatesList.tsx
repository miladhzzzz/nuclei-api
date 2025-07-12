import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface TemplatesListProps {
  templates: string[]
}

export function TemplatesList({ templates }: TemplatesListProps) {
  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>Templates Used</CardTitle>
      </CardHeader>
      <CardContent>
        {templates.length === 0 ? (
          <p className="text-muted-foreground">No templates have been used in this scan yet.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {templates.map((template) => (
              <Badge key={template} variant="secondary">
                {template}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

