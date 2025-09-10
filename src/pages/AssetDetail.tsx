import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeftIcon,
  PencilIcon,
  QrCodeIcon,
  DocumentIcon,
  CalendarIcon,
  CurrencyRupeeIcon,
  MapPinIcon,
  UserIcon,
} from '@heroicons/react/24/outline';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { format } from 'date-fns';

interface AssetDetail {
  id: number;
  name: string;
  category: {
    id: number;
    name: string;
    depreciation_rate: number;
  };
  serial_number: string;
  purchase_date: string;
  cost: number;
  current_value: number;
  status: string;
  brand: string;
  model: string;
  specifications: string;
  warranty_expiry: string;
  location: string;
  photo: string;
  qr_code: string;
  insurance_policy: string;
  insurance_expiry: string;
  documents: Array<{
    id: number;
    title: string;
    document: string;
    description: string;
    created_at: string;
  }>;
  assigned_to?: {
    id: number;
    name: string;
    employee_id: string;
    allocated_at: string;
  };
  allocation_history: Array<{
    employee_name: string;
    employee_id: string;
    allocated_at: string;
    returned_at: string;
    notes: string;
  }>;
  created_at: string;
  updated_at: string;
}

export default function AssetDetail() {
  const { id } = useParams<{ id: string }>();
  const { hasPermission } = useAuth();

  const { data: asset, isLoading } = useQuery<AssetDetail>({
    queryKey: ['asset', id],
    queryFn: async () => {
      const response = await api.get(`/assets/${id}/`);
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="bg-white shadow rounded-lg p-6 h-96"></div>
        </div>
      </div>
    );
  }

  if (!asset) {
    return (
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="text-center py-12">
          <div className="text-gray-500">Asset not found</div>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const statusStyles = {
      active: 'bg-green-100 text-green-800',
      maintenance: 'bg-yellow-100 text-yellow-800',
      retired: 'bg-red-100 text-red-800',
      disposed: 'bg-gray-100 text-gray-800',
    };
    
    return (
      <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${statusStyles[status as keyof typeof statusStyles] || 'bg-gray-100 text-gray-800'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Link
              to="/assets"
              className="mr-4 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <ArrowLeftIcon className="h-6 w-6" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{asset.name}</h1>
              <p className="mt-1 text-sm text-gray-600">
                {asset.category.name} • {asset.serial_number}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {getStatusBadge(asset.status)}
            {hasPermission('write') && (
              <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">
                <PencilIcon className="-ml-1 mr-2 h-5 w-5" />
                Edit
              </button>
            )}
            <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">
              <QrCodeIcon className="-ml-1 mr-2 h-5 w-5" />
              QR Code
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Asset Details */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Asset Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-500">Brand</label>
                <p className="mt-1 text-sm text-gray-900">{asset.brand || 'N/A'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Model</label>
                <p className="mt-1 text-sm text-gray-900">{asset.model || 'N/A'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Purchase Date</label>
                <p className="mt-1 text-sm text-gray-900 flex items-center">
                  <CalendarIcon className="h-4 w-4 mr-1 text-gray-400" />
                  {format(new Date(asset.purchase_date), 'MMM dd, yyyy')}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Warranty Expiry</label>
                <p className="mt-1 text-sm text-gray-900 flex items-center">
                  <CalendarIcon className="h-4 w-4 mr-1 text-gray-400" />
                  {asset.warranty_expiry ? format(new Date(asset.warranty_expiry), 'MMM dd, yyyy') : 'N/A'}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Location</label>
                <p className="mt-1 text-sm text-gray-900 flex items-center">
                  <MapPinIcon className="h-4 w-4 mr-1 text-gray-400" />
                  {asset.location || 'N/A'}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Insurance Policy</label>
                <p className="mt-1 text-sm text-gray-900">{asset.insurance_policy || 'N/A'}</p>
              </div>
            </div>
            
            {asset.specifications && (
              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-500">Specifications</label>
                <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{asset.specifications}</p>
              </div>
            )}
          </div>

          {/* Financial Information */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Financial Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-500">Original Cost</label>
                <p className="mt-1 text-lg font-semibold text-gray-900 flex items-center">
                  <CurrencyRupeeIcon className="h-5 w-5 mr-1 text-gray-400" />
                  {asset.cost.toLocaleString('en-IN')}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Current Value</label>
                <p className="mt-1 text-lg font-semibold text-green-600 flex items-center">
                  <CurrencyRupeeIcon className="h-5 w-5 mr-1 text-gray-400" />
                  {asset.current_value.toLocaleString('en-IN')}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Depreciation Rate</label>
                <p className="mt-1 text-lg font-semibold text-gray-900">
                  {asset.category.depreciation_rate}% per year
                </p>
              </div>
            </div>
          </div>

          {/* Allocation History */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Allocation History</h3>
            {asset.allocation_history.length > 0 ? (
              <div className="space-y-4">
                {asset.allocation_history.map((allocation, index) => (
                  <div key={index} className="border-l-4 border-blue-200 pl-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900 flex items-center">
                          <UserIcon className="h-4 w-4 mr-1 text-gray-400" />
                          {allocation.employee_name} ({allocation.employee_id})
                        </p>
                        <p className="text-xs text-gray-500">
                          {format(new Date(allocation.allocated_at), 'MMM dd, yyyy')} - 
                          {allocation.returned_at ? format(new Date(allocation.returned_at), 'MMM dd, yyyy') : 'Present'}
                        </p>
                      </div>
                    </div>
                    {allocation.notes && (
                      <p className="mt-1 text-sm text-gray-600">{allocation.notes}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No allocation history</p>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Current Assignment */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Current Assignment</h3>
            {asset.assigned_to ? (
              <div>
                <p className="text-sm font-medium text-gray-900 flex items-center">
                  <UserIcon className="h-4 w-4 mr-1 text-gray-400" />
                  {asset.assigned_to.name}
                </p>
                <p className="text-xs text-gray-500">{asset.assigned_to.employee_id}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Allocated: {format(new Date(asset.assigned_to.allocated_at), 'MMM dd, yyyy')}
                </p>
              </div>
            ) : (
              <p className="text-sm text-gray-500">Not currently assigned</p>
            )}
          </div>

          {/* Asset Photo */}
          {asset.photo && (
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Photo</h3>
              <img
                src={asset.photo}
                alt={asset.name}
                className="w-full h-48 object-cover rounded-lg"
              />
            </div>
          )}

          {/* QR Code */}
          {asset.qr_code && (
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">QR Code</h3>
              <img
                src={asset.qr_code}
                alt="QR Code"
                className="w-full h-48 object-contain bg-gray-50 rounded-lg"
              />
            </div>
          )}

          {/* Documents */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Documents</h3>
            {asset.documents.length > 0 ? (
              <div className="space-y-3">
                {asset.documents.map((doc) => (
                  <div key={doc.id} className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                    <DocumentIcon className="h-5 w-5 text-gray-400 mr-3" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{doc.title}</p>
                      <p className="text-xs text-gray-500">{format(new Date(doc.created_at), 'MMM dd, yyyy')}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No documents uploaded</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}