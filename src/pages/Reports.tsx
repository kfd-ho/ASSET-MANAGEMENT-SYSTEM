import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  DocumentArrowDownIcon,
  DocumentArrowUpIcon,
  ChartBarIcon,
  CurrencyRupeeIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import { api } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export default function Reports() {
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  const { data: depreciationReport } = useQuery({
    queryKey: ['depreciation-report', selectedYear],
    queryFn: async () => {
      const response = await api.get(`/reports/depreciation/?year=${selectedYear}`);
      return response.data;
    },
  });

  const { data: allocationReport } = useQuery({
    queryKey: ['allocation-report'],
    queryFn: async () => {
      const response = await api.get('/reports/allocation/');
      return response.data;
    },
  });

  const { data: maintenanceCostReport } = useQuery({
    queryKey: ['maintenance-cost-report', selectedYear],
    queryFn: async () => {
      const response = await api.get(`/reports/maintenance-cost/?year=${selectedYear}`);
      return response.data;
    },
  });

  const handleExportAssets = async () => {
    try {
      const response = await api.get('/reports/export/assets/', {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'assets_export.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Reports & Analytics</h1>
        <p className="mt-1 text-sm text-gray-600">
          Comprehensive reports and data insights for asset management
        </p>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={handleExportAssets}
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <DocumentArrowDownIcon className="h-8 w-8 text-blue-500 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Export Assets</p>
              <p className="text-sm text-gray-500">Download CSV</p>
            </div>
          </button>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <DocumentArrowUpIcon className="h-8 w-8 text-green-500 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Import Assets</p>
              <p className="text-sm text-gray-500">Upload CSV</p>
            </div>
          </button>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <ChartBarIcon className="h-8 w-8 text-purple-500 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Custom Report</p>
              <p className="text-sm text-gray-500">Generate report</p>
            </div>
          </button>
          
          <div className="flex items-center p-4 border border-gray-200 rounded-lg">
            <CalendarIcon className="h-8 w-8 text-orange-500 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Year</p>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="text-sm text-gray-500 border-none p-0 focus:ring-0"
              >
                {[2024, 2023, 2022, 2021].map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Depreciation Report */}
      {depreciationReport && (
        <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-medium text-gray-900">Depreciation Report - {selectedYear}</h3>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <div>Total Assets: {depreciationReport.summary.total_assets}</div>
              <div>Total Depreciation: ₹{depreciationReport.summary.total_depreciation?.toLocaleString('en-IN')}</div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                ₹{depreciationReport.summary.total_original_value?.toLocaleString('en-IN')}
              </div>
              <div className="text-sm text-gray-600">Original Value</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                ₹{depreciationReport.summary.total_current_value?.toLocaleString('en-IN')}
              </div>
              <div className="text-sm text-gray-600">Current Value</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                ₹{depreciationReport.summary.total_depreciation?.toLocaleString('en-IN')}
              </div>
              <div className="text-sm text-gray-600">Total Depreciation</div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Asset</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Original Value</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current Value</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Depreciation</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {depreciationReport.assets?.slice(0, 10).map((asset: any) => (
                  <tr key={asset.asset_id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{asset.asset_name}</div>
                      <div className="text-sm text-gray-500">{asset.serial_number}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {asset.category}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ₹{asset.original_value?.toLocaleString('en-IN')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ₹{asset.current_value?.toLocaleString('en-IN')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                      ₹{asset.depreciation?.toLocaleString('en-IN')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Maintenance Cost Report */}
      {maintenanceCostReport && (
        <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-6">
            Maintenance Cost Report - {selectedYear}
          </h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Monthly Costs Chart */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-4">Monthly Maintenance Costs</h4>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={maintenanceCostReport.monthly_costs}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`₹${value?.toLocaleString('en-IN')}`, 'Cost']} />
                  <Line type="monotone" dataKey="cost" stroke="#3b82f6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Category Costs */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-4">Cost by Category</h4>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={maintenanceCostReport.category_costs}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ asset__category__name, percent }) => 
                      `${asset__category__name} ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="total_cost"
                  >
                    {maintenanceCostReport.category_costs?.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`₹${value?.toLocaleString('en-IN')}`, 'Cost']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="mt-6 text-center">
            <div className="text-2xl font-bold text-gray-900">
              Total Maintenance Cost: ₹{maintenanceCostReport.total_cost?.toLocaleString('en-IN')}
            </div>
          </div>
        </div>
      )}

      {/* Allocation Report Summary */}
      {allocationReport && (
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Allocation Summary</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {allocationReport.total_allocations}
              </div>
              <div className="text-sm text-gray-600">Total Allocations</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {allocationReport.active_allocations}
              </div>
              <div className="text-sm text-gray-600">Active Allocations</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-600">
                {allocationReport.returned_allocations}
              </div>
              <div className="text-sm text-gray-600">Returned Assets</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}