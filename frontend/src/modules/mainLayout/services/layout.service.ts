import api from "@/shared/libs/axios";
import { UserDataResponse } from "../types/user.types";

export async function getUserData(): Promise<UserDataResponse> {
    const response = await api.get<UserDataResponse>('usuarios/me');
    return response.data;
}