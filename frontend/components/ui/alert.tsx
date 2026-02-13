"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const alertVariants = cva("flex items-center gap-2 rounded-md border px-4 py-3 text-sm", {
  variants: {
    variant: {
      default: "border-primary/20 bg-primary/10 text-primary",
      destructive: "border-destructive/20 bg-destructive/10 text-destructive",
    },
  },
  defaultVariants: {
    variant: "default",
  },
})

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof alertVariants> {}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(({ className, variant, children, ...props }, ref) => (
  <div ref={ref} className={cn(alertVariants({ variant }), className)} {...props}>
    {children}
  </div>
))
Alert.displayName = "Alert"

const AlertTitle = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>((props, ref) => (
  <h3 ref={ref} className="font-medium" {...props} />
))
AlertTitle.displayName = "AlertTitle"

const AlertDescription = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>((props, ref) => (
  <p ref={ref} className="text-sm" {...props} />
))
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertDescription, AlertTitle }

