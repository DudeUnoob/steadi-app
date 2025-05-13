"use client"

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/components/ui/use-toast"
import { ArrowLeft, ArrowRight, Shield, ShieldCheck } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface Permission {
    id: string
    label: string
    description: string
    checked: boolean
}

export default function RulesPage() {
    const navigate = useNavigate()
    const { toast } = useToast()
    const [activeTab, setActiveTab] = useState<string>("staff")
    const [isSubmitting, setIsSubmitting] = useState(false)

    const [staffPermissions, setStaffPermissions] = useState<Permission[]>([
        {
            id: "staff-view-products",
            label: "View Products",
            description: "Allow staff to view product information",
            checked: true,
        },
        {
            id: "staff-edit-products",
            label: "Edit Products",
            description: "Allow staff to edit product information",
            checked: false,
        },
        {
            id: "staff-view-suppliers",
            label: "View Suppliers",
            description: "Allow staff to view supplier information",
            checked: true,
        },
        {
            id: "staff-edit-suppliers",
            label: "Edit Suppliers",
            description: "Allow staff to edit supplier information",
            checked: false,
        },
        {
            id: "staff-view-sales",
            label: "View Sales",
            description: "Allow staff to view sales information",
            checked: true,
        },
        {
            id: "staff-edit-sales",
            label: "Edit Sales",
            description: "Allow staff to edit sales information",
            checked: false,
        },
    ])

    const [managerPermissions, setManagerPermissions] = useState<Permission[]>([
        {
            id: "manager-view-products",
            label: "View Products",
            description: "Allow managers to view product information",
            checked: true,
        },
        {
            id: "manager-edit-products",
            label: "Edit Products",
            description: "Allow managers to edit product information",
            checked: true,
        },
        {
            id: "manager-view-suppliers",
            label: "View Suppliers",
            description: "Allow managers to view supplier information",
            checked: true,
        },
        {
            id: "manager-edit-suppliers",
            label: "Edit Suppliers",
            description: "Allow managers to edit supplier information",
            checked: true,
        },
        {
            id: "manager-view-sales",
            label: "View Sales",
            description: "Allow managers to view sales information",
            checked: true,
        },
        {
            id: "manager-edit-sales",
            label: "Edit Sales",
            description: "Allow managers to edit sales information",
            checked: true,
        },
        {
            id: "manager-set-staff-rules",
            label: "Set Staff Rules",
            description: "Allow managers to set permissions for staff members",
            checked: true,
        },
    ])

    const togglePermission = (id: string, isStaff: boolean) => {
        if (isStaff) {
            setStaffPermissions(
                staffPermissions.map((permission) =>
                    permission.id === id ? { ...permission, checked: !permission.checked } : permission,
                ),
            )
        } else {
            setManagerPermissions(
                managerPermissions.map((permission) =>
                    permission.id === id ? { ...permission, checked: !permission.checked } : permission,
                ),
            )
        }
    }

    const handleSubmit = async () => {
        setIsSubmitting(true)

        try {
            // Simulate API call
            await new Promise((resolve) => setTimeout(resolve, 1500))

            toast({
                title: "Permissions saved",
                description: "Role permissions have been successfully configured.",
            })

            navigate("/dashboard")
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to save permissions. Please try again.",
                variant: "destructive",
            })
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleSkip = () => {
        toast({
            title: "Default permissions applied",
            description: "You can update role permissions later in settings.",
        })

        navigate("/dashboard")
    }

    return (
        <div className="flex min-h-screen w-full flex-col items-center justify-center bg-background p-4">
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute left-1/4 top-1/4 h-[500px] w-[500px] rounded-full bg-steadi-red/10 blur-[100px]" />
                <div className="absolute bottom-1/4 right-1/4 h-[600px] w-[600px] rounded-full bg-steadi-purple/10 blur-[100px]" />
                <div className="absolute left-1/2 top-1/2 h-[300px] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-steadi-pink/10 blur-[100px]" />
                <div className="absolute inset-0 grid-pattern opacity-20" />
            </div>

            <div className="z-10 w-full max-w-3xl">
                <div className="flex flex-col items-center space-y-2 text-center">
                    <div className="flex items-center justify-center space-x-2">
                        <div className="relative flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-steadi-red via-steadi-pink to-steadi-purple p-[1px]">
                            <div className="flex h-full w-full items-center justify-center rounded-full bg-black">
                                <Shield className="h-6 w-6 text-white" />
                            </div>
                        </div>
                        <span className="text-3xl font-bold steadi-gradient-text">Steadi.</span>
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight">Configure Role Permissions</h1>
                    <p className="text-sm text-muted-foreground">Set up permissions for your organization members</p>
                </div>

                <Card className="mt-8 overflow-hidden border-0 bg-black/40 backdrop-blur-xl">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <ShieldCheck className="h-5 w-5 text-steadi-pink" />
                            Role Permissions
                        </CardTitle>
                        <CardDescription>Define what each role can access and modify in your organization</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                            <TabsList className="grid w-full grid-cols-2">
                                <TabsTrigger value="staff">Staff Permissions</TabsTrigger>
                                <TabsTrigger value="manager">Manager Permissions</TabsTrigger>
                            </TabsList>

                            <TabsContent value="staff" className="mt-6 space-y-4">
                                {staffPermissions.map((permission) => (
                                    <div
                                        key={permission.id}
                                        className="flex items-start space-x-3 rounded-md border border-[#2a2a30] bg-muted/20 p-4 transition-colors hover:bg-muted/30"
                                    >
                                        <Checkbox
                                            id={permission.id}
                                            checked={permission.checked}
                                            onCheckedChange={() => togglePermission(permission.id, true)}
                                            className="mt-1 data-[state=checked]:bg-steadi-pink data-[state=checked]:border-steadi-pink"
                                        />
                                        <div className="space-y-1">
                                            <label
                                                htmlFor={permission.id}
                                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                                            >
                                                {permission.label}
                                            </label>
                                            <p className="text-xs text-muted-foreground">{permission.description}</p>
                                        </div>
                                    </div>
                                ))}
                            </TabsContent>

                            <TabsContent value="manager" className="mt-6 space-y-4">
                                {managerPermissions.map((permission) => (
                                    <div
                                        key={permission.id}
                                        className="flex items-start space-x-3 rounded-md border border-[#2a2a30] bg-muted/20 p-4 transition-colors hover:bg-muted/30"
                                    >
                                        <Checkbox
                                            id={permission.id}
                                            checked={permission.checked}
                                            onCheckedChange={() => togglePermission(permission.id, false)}
                                            className="mt-1 data-[state=checked]:bg-steadi-pink data-[state=checked]:border-steadi-pink"
                                        />
                                        <div className="space-y-1">
                                            <label
                                                htmlFor={permission.id}
                                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                                            >
                                                {permission.label}
                                            </label>
                                            <p className="text-xs text-muted-foreground">{permission.description}</p>
                                        </div>
                                    </div>
                                ))}
                            </TabsContent>
                        </Tabs>
                    </CardContent>
                    <CardFooter className="flex justify-between border-t border-[#2a2a30] bg-muted/10 px-6 py-4">
                        <Button variant="outline" onClick={handleSkip} className="border-[#2a2a30] bg-transparent">
                            <ArrowLeft className="mr-2 h-4 w-4" />
                            Skip for now
                        </Button>
                        <Button onClick={handleSubmit} className="bg-steadi-pink hover:bg-steadi-pink/90" disabled={isSubmitting}>
                            {isSubmitting ? "Saving..." : "Save & Continue"}
                            {!isSubmitting && <ArrowRight className="ml-2 h-4 w-4" />}
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        </div>
    )
}
