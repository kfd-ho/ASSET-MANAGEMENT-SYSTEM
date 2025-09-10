import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  CubeIcon,
  UsersIcon,
  ArrowsRightLeftIcon,
  WrenchScrewdriverIcon,
  CurrencyRupeeIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';

interface DashboardStats {
  assets: {
    total: number;
    active: number;
    maintenance: number;
    retired: number;
    total_value: number;
    current_value: number;
    depreciation_this_year: number;
  };
  allocations: {
    total: number;
    active: number;
    this_month: number;
  };
  maintenance: {
    this_month: number;
    cost_this_year: number;
  };
  employees: {
    total: number;
    with_assets: number;
  };
  category_breakdown: Array<{
    category__name: string;
    count: number;
    total_value: number;
    current_value: number;
  }>;
  monthly_trends: Array<{
    month: string;
    assets_purchased: number;
    allocations: number;
    maintenance_cost: number;
  }>;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export default function Dashboard() {
  const { user } = useAuth();

  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/reports/dashboard/');
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white p-6 rounded-lg shadow h-32"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const statCards = [
    {
      name: 'Total Assets',
      value: stats?.assets.total || 0,
      icon: CubeIcon,
      color: 'bg-blue-500',
      subtext: `₹${(stats?.assets.total_value || 0).toLocaleString('en-IN')} total value`,
    },
    {
      name: 'Active Allocations',
      value: stats?.allocations.active || 0,
      icon: ArrowsRightLeftIcon,
      color: 'bg-green-500',
      subtext: `${stats?.allocations.this_month || 0} this month`,
    },
    {
      name: 'Employees',
      value: stats?.employees.total || 0,
      icon: UsersIcon,
      color: 'bg-purple-500',
      subtext: `${stats?.employees.with_assets || 0} with assets`,
    },
    {
      name: 'Maintenance Cost',
      value: `₹${(stats?.maintenance.cost_this_year || 0).toLocaleString('en-IN')}`,
      icon: WrenchScrewdriverIcon,
      color: 'bg-orange-500',
      subtext: 'This year',
    },
  ];

  const assetStatusData = [
    { name: 'Active', value: stats?.assets.active || 0, color: '#10b981' },
    { name: 'Maintenance', value: stats?.assets.maintenance || 0, color: '#f59e0b' },
    { name: 'Retired', value: stats?.assets.retired || 0, color: '#ef4444' },
  ];

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Welcome back, {user?.first_name}! Here's what's happening with your assets.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {statCards.map((stat) => (
          <div key={stat.name} className="bg-white overflow-hidden shadow-sm rounded-lg hover:shadow-md transition-shadow">
            <div className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`${stat.color} p-3 rounded-lg`}>
                    <stat.icon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <div className="ml-4 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">{stat.name}</dt>
                    <dd className="text-2xl font-bold text-gray-900">{stat.value}</dd>
                    <dd className="text-xs text-gray-500">{stat.subtext}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Asset Status Distribution */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Asset Status Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={assetStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {assetStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Monthly Trends */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Monthly Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats?.monthly_trends || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="assets_purchased" stroke="#3b82f6" name="Assets Purchased" />
              <Line type="monotone" dataKey="allocations" stroke="#10b981" name="Allocations" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Assets by Category</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={stats?.category_breakdown || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category__name" />
            <YAxis />
            <Tooltip formatter={(value, name) => [value, name === 'count' ? 'Assets' : 'Value (₹)']} />
            <Bar dataKey="count" fill="#3b82f6" name="count" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <CubeIcon className="h-8 w-8 text-blue-500 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Add Asset</p>
              <p className="text-sm text-gray-500">Register new asset</p>
            </div>
          </button>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <ArrowsRightLeftIcon className="h-8 w-8 text-green-500 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Allocate Asset</p>
              <p className="text-sm text-gray-500">Assign to employee</p>
            </div>
          </button>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <WrenchScrewdriverIcon className="h-8 w-8 text-orange-500 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Schedule Maintenance</p>
              <p className="text-sm text-gray-500">Plan maintenance task</p>
            </div>
          </button>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <CurrencyRupeeIcon className="h-8 w-8 text-purple-500 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">View Reports</p>
              <p className="text-sm text-gray-500">Financial reports</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}