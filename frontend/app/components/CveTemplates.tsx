import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface CveTemplatesProps {
  templates: string[]
}

export function CveTemplates({ templates }: CveTemplatesProps) {
  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>CVE Templates Used</CardTitle>
      </CardHeader>
      <CardContent>
        {templates.length === 0 ? (
          <p className="text-muted-foreground">No CVE templates were used in this scan.</p>
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

