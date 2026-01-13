import api from "@/api/axios";
import { UserDataResponse } from "../types/user.types";

export async function getUserData(): Promise<UserDataResponse> {
    const response = await api.get<UserDataResponse>('usuarios/me');
    return response.data;
}