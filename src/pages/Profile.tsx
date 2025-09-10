import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { UserCircleIcon, EnvelopeIcon, IdentificationIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline';

export default function Profile() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage your account information and preferences
          </p>
        </div>

        <div className="bg-white shadow-sm rounded-lg overflow-hidden">
          <div className="px-6 py-8">
            <div className="flex items-center">
              <div className="h-20 w-20 bg-blue-100 rounded-full flex items-center justify-center">
                <UserCircleIcon className="h-12 w-12 text-blue-600" />
              </div>
              <div className="ml-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  {user.first_name} {user.last_name}
                </h2>
                <p className="text-sm text-gray-600 capitalize">
                  {user.role} • @{user.username}
                </p>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-200 px-6 py-6">
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-gray-500 flex items-center">
                  <EnvelopeIcon className="h-4 w-4 mr-2" />
                  Email Address
                </dt>
                <dd className="mt-1 text-sm text-gray-900">{user.email}</dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 flex items-center">
                  <IdentificationIcon className="h-4 w-4 mr-2" />
                  Employee ID
                </dt>
                <dd className="mt-1 text-sm text-gray-900">{user.employee_id || 'N/A'}</dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 flex items-center">
                  <BuildingOfficeIcon className="h-4 w-4 mr-2" />
                  Department
                </dt>
                <dd className="mt-1 text-sm text-gray-900">{user.department || 'N/A'}</dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500">Role</dt>
                <dd className="mt-1">
                  <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 capitalize">
                    {user.role}
                  </span>
                </dd>
              </div>
            </dl>
          </div>

          <div className="border-t border-gray-200 px-6 py-4">
            <div className="flex justify-end">
              <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">
                Edit Profile
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}