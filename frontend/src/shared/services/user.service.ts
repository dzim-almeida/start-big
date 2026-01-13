import api from "@/api/axios";

import { UserResponse } from "../types/auth.types";

export async function getUser(): Promise<UserResponse> {
    const response = await api.get<UserResponse>('usuarios/me');
    return response.data;
}