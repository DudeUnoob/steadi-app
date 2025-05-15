"use client"

import { useState, useEffect } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/components/ui/use-toast"
import { ArrowLeft, ArrowRight, Shield, ShieldCheck, Building } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { useAuth } from "../../lib/AuthContext"
import { supabase } from "../../lib/supabase"

// API URL for backend communication
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Permission {
    id: string
    label: string
    description: string
    checked: boolean
}

interface RulesData {
    staff_view_products: boolean;
    staff_edit_products: boolean;
    staff_view_suppliers: boolean;
    staff_edit_suppliers: boolean;
    staff_view_sales: boolean;
    staff_edit_sales: boolean;
    manager_view_products: boolean;
    manager_edit_products: boolean;
    manager_view_suppliers: boolean;
    manager_edit_suppliers: boolean;
    manager_view_sales: boolean;
    manager_edit_sales: boolean;
    manager_set_staff_rules: boolean;
}

// New component for displaying organization ID with copy functionality
const OrganizationIdDisplay = ({ 
    organizationId,
}: { 
    organizationId: string, 
}) => {
    const [copied, setCopied] = useState(false);
    
    const copyToClipboard = () => {
        if (organizationId) {
            navigator.clipboard.writeText(organizationId);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };
    
    return (
        <div className="px-6 py-2 border-b border-[#2a2a30] bg-muted/10">
            <div className="flex flex-col space-y-1">
                <div className="flex items-center space-x-2">
                    <Building className="h-4 w-4 text-steadi-pink" />
                    <h3 className="text-sm font-medium">Organization ID</h3>
                </div>
                <div className="relative">
                    <div className="flex space-x-2">
                        <div className="relative flex-grow">
                            <Input
                                type="text"
                                placeholder="Organization ID (will be displayed or generated)"
                                value={organizationId}
                                readOnly
                                className="bg-muted/50 border-[#2a2a30] focus-visible:ring-steadi-pink"
                            />
                        </div>
                        {organizationId && (
                            <Button 
                                type="button" 
                                variant="outline" 
                                size="sm"
                                onClick={copyToClipboard}
                                className="h-10 bg-muted/50 border-[#2a2a30] hover:bg-muted/70"
                            >
                                {copied ? "Copied!" : "Copy"}
                            </Button>
                        )}
                    </div>
                </div>
                <p className="text-xs text-muted-foreground">
                    {!organizationId 
                        ? "A unique 6-digit ID will be generated and displayed here upon saving."
                        : "This is your organization's unique ID. Staff members can use it to join."}
                </p>
            </div>
        </div>
    );
};

// Helper function to make authenticated API calls with auto-retry on 401
const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
    // First, get a fresh token
    console.log('Getting fresh token from Supabase...');
    const { data: { session }, error: sessionError } = await supabase.auth.getSession();
    
    if (sessionError) {
        console.error('Error getting session:', sessionError);
        throw new Error(`Failed to get authentication session: ${sessionError.message}`);
    }
    
    const token = session?.access_token;
    
    if (!token) {
        console.error('No access token available in session:', session);
        throw new Error('No valid authentication token available');
    }
    
    console.log(`Retrieved token (length: ${token.length})`);
    
    // Add token to headers
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    
    console.log(`Making ${options.method || 'GET'} request to ${url}...`);
    
    // Make the initial request
    let response: Response;
    try {
        response = await fetch(url, {
            ...options,
            headers
        });
    } catch (error) {
        console.error('Network error during fetch:', error);
        throw new Error(`Network error: ${error instanceof Error ? error.message : String(error)}`);
    }
    
    console.log(`Initial response status: ${response.status}`);
    
    // If unauthorized, try to refresh the token and retry once
    if (response.status === 401) {
        console.log('Received 401, attempting token refresh...');
        
        const { data: refreshResult, error: refreshError } = await supabase.auth.refreshSession();
        
        if (refreshError || !refreshResult.session) {
            console.error('Token refresh failed:', refreshError);
            throw new Error(`Authentication failed: ${refreshError?.message || 'Unable to refresh token'}`);
        }
        
        console.log('Token refreshed successfully, retrying request...');
        
        // Retry with new token
        try {
            response = await fetch(url, {
                ...options,
                headers: {
                    ...options.headers,
                    'Authorization': `Bearer ${refreshResult.session.access_token}`
                }
            });
            console.log(`Retry response status: ${response.status}`);
        } catch (error) {
            console.error('Network error during retry fetch:', error);
            throw new Error(`Network error on retry: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    
    // Check final response
    if (!response.ok) {
        // Clone response and get both text and possible JSON for better debugging
        const clonedResponse = response.clone();
        const errorText = await response.text();
        
        try {
            // Try to parse as JSON for more details
            const errorJson = JSON.parse(errorText);
            console.error(`API error (${response.status})`, errorJson);
            throw new Error(`Server error: ${response.status} - ${errorJson.detail || JSON.stringify(errorJson)}`);
        } catch (e) {
            // If not JSON or JSON parsing failed
            console.error(`API error (${response.status}):`, errorText);
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }
    }
    
    return response;
};

export default function RulesPage() {
    const navigate = useNavigate()
    const location = useLocation()
    const { toast } = useToast()
    const { user, session } = useAuth()
    const [activeTab, setActiveTab] = useState<string>("staff")
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [isLoading, setIsLoading] = useState(true)
    const [organizationId, setOrganizationId] = useState<string>('')

    // Load initial rules data from API
    useEffect(() => {
        const fetchRules = async () => {
            setIsLoading(true);
            
            try {
                const response = await fetchWithAuth(`${API_URL}/rules/me`);
                const data = await response.json();
                
                // Set organization ID if available
                if (data.organization_id) {
                    setOrganizationId(data.organization_id.toString());
                }
                
                // Update permission states
                updatePermissionStates(data);
            } catch (error) {
                console.error('Error fetching rules:', error);
                toast({
                    title: "Error",
                    description: "Failed to load your settings. Please try again.",
                    variant: "destructive",
                });
            } finally {
                setIsLoading(false);
            }
        };
        
        fetchRules();
    }, []);

    // Update permission states from API data
    const updatePermissionStates = (data: RulesData) => {
        // Update staff permissions
        setStaffPermissions([
            {
                id: "staff-view-products",
                label: "View Products",
                description: "Allow staff to view product information",
                checked: data.staff_view_products,
            },
            {
                id: "staff-edit-products",
                label: "Edit Products",
                description: "Allow staff to edit product information",
                checked: data.staff_edit_products,
            },
            {
                id: "staff-view-suppliers",
                label: "View Suppliers",
                description: "Allow staff to view supplier information",
                checked: data.staff_view_suppliers,
            },
            {
                id: "staff-edit-suppliers",
                label: "Edit Suppliers",
                description: "Allow staff to edit supplier information",
                checked: data.staff_edit_suppliers,
            },
            {
                id: "staff-view-sales",
                label: "View Sales",
                description: "Allow staff to view sales information",
                checked: data.staff_view_sales,
            },
            {
                id: "staff-edit-sales",
                label: "Edit Sales",
                description: "Allow staff to edit sales information",
                checked: data.staff_edit_sales,
            },
        ]);
        
        // Update manager permissions
        setManagerPermissions([
            {
                id: "manager-view-products",
                label: "View Products",
                description: "Allow managers to view product information",
                checked: data.manager_view_products,
            },
            {
                id: "manager-edit-products",
                label: "Edit Products",
                description: "Allow managers to edit product information",
                checked: data.manager_edit_products,
            },
            {
                id: "manager-view-suppliers",
                label: "View Suppliers",
                description: "Allow managers to view supplier information",
                checked: data.manager_view_suppliers,
            },
            {
                id: "manager-edit-suppliers",
                label: "Edit Suppliers",
                description: "Allow managers to edit supplier information",
                checked: data.manager_edit_suppliers,
            },
            {
                id: "manager-view-sales",
                label: "View Sales",
                description: "Allow managers to view sales information",
                checked: data.manager_view_sales,
            },
            {
                id: "manager-edit-sales",
                label: "Edit Sales",
                description: "Allow managers to edit sales information",
                checked: data.manager_edit_sales,
            },
            {
                id: "manager-set-staff-rules",
                label: "Set Staff Rules",
                description: "Allow managers to set permissions for staff members",
                checked: data.manager_set_staff_rules,
            },
        ]);
    };

    // Check if the user should be on this page
    useEffect(() => {
        const rulesSetupRequired = localStorage.getItem('rules_setup_required');
        
        // If the user tries to access this page without coming from email verification
        // and they've already completed setup, redirect to dashboard
        if (rulesSetupRequired !== 'true' && localStorage.getItem('rules_setup_completed') === 'true') {
            navigate('/dashboard');
            return;
        }
        
        // If the user tries to navigate away from this page before completing setup
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (localStorage.getItem('rules_setup_required') === 'true' && 
                localStorage.getItem('rules_setup_completed') !== 'true') {
                e.preventDefault();
                e.returnValue = '';
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        
        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
        };
    }, [navigate]);

    // Force redirect back to rules page if user tries to navigate elsewhere
    useEffect(() => {
        const handleLocationChange = () => {
            if (
                localStorage.getItem('rules_setup_required') === 'true' && 
                localStorage.getItem('rules_setup_completed') !== 'true' &&
                !location.pathname.includes('/auth/rules')
            ) {
                navigate('/auth/rules');
            }
        };

        window.addEventListener('popstate', handleLocationChange);
        
        return () => {
            window.removeEventListener('popstate', handleLocationChange);
        };
    }, [navigate, location]);

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
        setIsSubmitting(true);

        try {
            // Prepare data from permission states
            const rulesOnlyData: Omit<RulesData, 'organization_id'> = {
                staff_view_products: staffPermissions.find(p => p.id === "staff-view-products")?.checked || false,
                staff_edit_products: staffPermissions.find(p => p.id === "staff-edit-products")?.checked || false,
                staff_view_suppliers: staffPermissions.find(p => p.id === "staff-view-suppliers")?.checked || false,
                staff_edit_suppliers: staffPermissions.find(p => p.id === "staff-edit-suppliers")?.checked || false,
                staff_view_sales: staffPermissions.find(p => p.id === "staff-view-sales")?.checked || false,
                staff_edit_sales: staffPermissions.find(p => p.id === "staff-edit-sales")?.checked || false,
                
                manager_view_products: managerPermissions.find(p => p.id === "manager-view-products")?.checked || true,
                manager_edit_products: managerPermissions.find(p => p.id === "manager-edit-products")?.checked || true,
                manager_view_suppliers: managerPermissions.find(p => p.id === "manager-view-suppliers")?.checked || true,
                manager_edit_suppliers: managerPermissions.find(p => p.id === "manager-edit-suppliers")?.checked || true,
                manager_view_sales: managerPermissions.find(p => p.id === "manager-view-sales")?.checked || true,
                manager_edit_sales: managerPermissions.find(p => p.id === "manager-edit-sales")?.checked || true,
                manager_set_staff_rules: managerPermissions.find(p => p.id === "manager-set-staff-rules")?.checked || true,
            };
            
            // Use our helper function to handle auth and retries
            const response = await fetchWithAuth(`${API_URL}/rules/me`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(rulesOnlyData)
            });
            
            // Extract and set the organization ID. The response now includes organization_id at the top level.
            const responseData = await response.json();
            if (responseData.organization_id && (!organizationId || organizationId.trim() === '')) {
                setOrganizationId(responseData.organization_id.toString());
            }

            // Mark rules setup as completed
            localStorage.setItem('rules_setup_required', 'false');
            localStorage.setItem('rules_setup_completed', 'true');

            toast({
                title: "Permissions saved",
                description: responseData.organization_id 
                    ? "Role permissions have been successfully configured."
                    : `Role permissions saved with organization ID: ${responseData.organization_id}`,
            });

            // Small delay to show the generated organization ID before navigating
            if (!organizationId || organizationId.trim() === '') {
                setTimeout(() => {
                    navigate("/dashboard");
                }, 1500);
            } else {
                navigate("/dashboard");
            }
        } catch (error) {
            console.error('Error saving rules:', error);
            toast({
                title: "Error",
                description: error instanceof Error ? error.message : "Failed to save permissions. Please try again.",
                variant: "destructive",
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    // Add back the skip function
    const handleSkip = () => {
        // Mark rules setup as completed even when skipped
        localStorage.setItem('rules_setup_required', 'false');
        localStorage.setItem('rules_setup_completed', 'true');
        
        toast({
            title: "Default permissions applied",
            description: "You can update role permissions later in settings.",
        });

        navigate("/dashboard");
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gradient-to-r from-[#ff5757] to-[#8c52ff] flex justify-center items-center">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg border border-black/20 p-8 max-w-md w-full text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-black mx-auto"></div>
                    <p className="mt-4 text-black font-['Poppins']">Loading your settings...</p>
                </div>
            </div>
        );
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
                        <CardDescription>
                            Define what each role can access and modify in your organization.
                            You can configure these settings now or customize them later.
                        </CardDescription>
                    </CardHeader>
                    
                    {/* Organization ID Section */}
                    <OrganizationIdDisplay
                        organizationId={organizationId}
                    />
                    
                    <CardContent className="pt-6">
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
